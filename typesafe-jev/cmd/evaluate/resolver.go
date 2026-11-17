package main

// config.go owns backend rows and setting validation. Runtime resolution lives
// here because it composes those settings with credentials and client startup;
// putting that work in the backend-spec owner would mix data with runtime state.

import (
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// resolvedHop is a configured destination with its one credential load. Config
// remains value-free; only this runtime result retains a redacting credential.
type resolvedHop struct {
	config Config
	loaded loadedCredential
}

type resolvedHops struct {
	config Config
	hops   []resolvedHop
}

// resolveHops returns the configured ordered list, including the
// verdict for an unusable hop so --check can remain stricter than the server.
func resolveHops(look lookupFunc, pluginDefaults bool) (resolvedHops, error) {
	cfg, err := resolveHopConfig(look, pluginDefaults)
	if err != nil {
		return resolvedHops{}, err
	}
	return resolveConfiguredHops(cfg, look), nil
}

// chainConfigs is the one walk of a Config's hops in chain order: the first
// hop, the fallback, then any later hops.
func (c Config) chainConfigs() []Config {
	configs := []Config{c}
	if c.Fallback != nil {
		configs = append(configs, c.fallbackConfig())
	}
	return append(configs, c.AdditionalHops...)
}

func resolveConfiguredHops(cfg Config, look lookupFunc) resolvedHops {
	r := resolvedHops{config: cfg}
	for _, hop := range cfg.chainConfigs() {
		r.hops = append(r.hops, resolvedHop{config: hop, loaded: loadCredentialSource(hop, look)})
	}
	return r
}

// resolveConfig retains the legacy pair entry point used by single-backend
// callers. Runtime and setup use resolveHopConfig for chain precedence.
func resolveConfig(look lookupFunc) (Config, error) {
	return resolveLegacyConfig(look, false)
}

func resolveCallConfig(look lookupFunc, pluginDefaults bool) (Config, error) {
	return resolveHopConfig(look, pluginDefaults)
}

// resolveHopConfig uses the same precedence for setup, call and the server.
// Legacy settings are resolved unchanged, including their existing diagnostics.
func resolveHopConfig(look lookupFunc, pluginDefaults bool) (Config, error) {
	raw, chainSet := look("JEV_CHAIN")
	_, primarySet := look("JEV_PROVIDER")
	fallback, _ := look("JEV_FALLBACK_PROVIDER")
	fallbackSet := fallback != ""
	if chainSet && (primarySet || fallbackSet) {
		return Config{}, fmt.Errorf("JEV_CHAIN cannot be combined with JEV_PROVIDER or JEV_FALLBACK_PROVIDER")
	}
	if !chainSet && (primarySet || fallbackSet) {
		return resolveLegacyConfig(look, pluginDefaults)
	}
	raw, source, err := chainSetting(look, raw, chainSet, pluginDefaults)
	if err != nil {
		return Config{}, err
	}
	names, err := parseChain(raw, source)
	if err != nil {
		return Config{}, err
	}
	pair := func(key string) (string, bool) {
		switch key {
		case "JEV_PROVIDER":
			return names[0], true
		case "JEV_FALLBACK_PROVIDER":
			if len(names) > 1 {
				return names[1], true
			}
			return "", false
		}
		return look(key)
	}
	cfg, err := resolveLegacyConfig(pair, pluginDefaults)
	if err != nil {
		return cfg, err
	}
	home := pluginHome(look, pluginDefaults)
	for i := 2; i < len(names); i++ {
		name := names[i]
		// Hops 3 and 4 have no key-file variable, so none is read or named.
		keyFile, defaulted, err := resolveHopKeyFile(nil, "", name, home)
		if err != nil {
			return cfg, err
		}
		hop := cfg.laterHop(providers[name], keyFile, defaulted)
		hop.defaultKeyOnly = true
		cfg.AdditionalHops = append(cfg.AdditionalHops, hop)
	}
	return cfg, nil
}

// chainSetting reads the file only after environment precedence is settled.
func chainSetting(look lookupFunc, raw string, chainSet, pluginDefaults bool) (string, string, error) {
	if chainSet {
		return raw, "JEV_CHAIN", nil
	}
	if home := homeDir(look); filepath.IsAbs(home) {
		path := filepath.Join(home, filepath.FromSlash(pluginKeyDirectory), "chain")
		data, err := readChainFile(path)
		if err == nil {
			return strings.TrimSpace(string(data)), "chain file", nil
		}
		if !errors.Is(err, os.ErrNotExist) {
			return "", "", fmt.Errorf("reading chain file: %w", err)
		}
	}
	if pluginDefaults {
		return defaultProvider + ",openrouter", "built-in chain", nil
	}
	return defaultProvider, "built-in chain", nil
}

func readChainFile(path string) ([]byte, error) {
	f, _, err := openRegularFile(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return io.ReadAll(f)
}

// resolveLegacyConfig validates the existing provider/pair settings.
// Setup deliberately resolves settings without opening any credential file.
func resolveLegacyConfig(look lookupFunc, pluginDefaults bool) (Config, error) {
	var cfg Config
	home := pluginHome(look, pluginDefaults)

	spec, err := resolveProvider(look)
	if err != nil {
		return cfg, err
	}
	cfg.Provider = spec

	if cfg.Model, err = resolveModel(look, spec); err != nil {
		return cfg, err
	}
	if cfg.Timeout, err = resolveTimeout(look); err != nil {
		return cfg, err
	}
	if cfg.HopTimeout, err = resolveHopTimeout(look, cfg.Timeout); err != nil {
		return cfg, err
	}
	if cfg.MaxRetries, err = resolveMaxRetries(look); err != nil {
		return cfg, err
	}
	if cfg.KeyFile, cfg.KeyFileDefaulted, err = resolveHopKeyFile(look, pluginKeyFileEnv, spec.Name, home); err != nil {
		return cfg, err
	}
	if cfg.Fallback, err = resolveFallback(look, spec, home); err != nil {
		return cfg, err
	}
	if cfg.AllowImages, err = resolveOptIn(look, "JEV_IMAGES"); err != nil {
		return cfg, err
	}
	if cfg.LongContext, err = resolveOptIn(look, "JEV_LONG_CONTEXT"); err != nil {
		return cfg, err
	}

	return cfg, nil
}

// pluginHome is the key-file discovery root, which only --plugin-defaults enables.
func pluginHome(look lookupFunc, pluginDefaults bool) string {
	if !pluginDefaults {
		return ""
	}
	return homeDir(look)
}

// homeDir is $HOME, or the platform's home directory when HOME is unset.
func homeDir(look lookupFunc) string {
	if home, ok := look("HOME"); ok && home != "" {
		return home
	}
	home, _ := os.UserHomeDir()
	return home
}

// resolveHopKeyFile applies discovery only after provider selection, and
// validates a discovered path at the same point as an explicit path. This keeps
// diagnostics stable when more than one setting is invalid. An empty name
// means the hop has no key-file variable and uses discovery alone.
func resolveHopKeyFile(look lookupFunc, name, provider, home string) (string, bool, error) {
	if providers[provider].AuthKind == authNone {
		return "", false, nil
	}
	if name != "" {
		path, err := resolveKeyFileVar(look, name)
		if err != nil || path != "" {
			return path, false, err
		}
	}
	if home == "" {
		return "", false, nil
	}
	candidate := filepath.Join(home, filepath.FromSlash(pluginKeyDirectory), provider+".key")
	if _, err := os.Lstat(candidate); err != nil {
		return "", false, nil
	}
	label := name
	if label == "" {
		label = "the default key file"
	}
	path, err := resolveKeyFileVar(func(string) (string, bool) { return candidate, true }, label)
	return path, true, err
}

// report keeps the legacy primary/fallback fields and exposes longer chains.
func (r resolvedHops) report() checkReport {
	report := checkReport{Exit: r.credentialExit(), Primary: r.hops[0].loaded.status}
	if len(r.hops) > 1 {
		fallback := r.hops[1].loaded.status
		report.Fallback = &fallback
	}
	if len(r.hops) > 2 {
		for _, hop := range r.hops {
			report.Hops = append(report.Hops, hop.loaded.status)
		}
	}
	return report
}

func (r resolvedHops) reportUnusable(out io.Writer) {
	for _, hop := range r.hops {
		s := hop.loaded.status
		if s.State == "unusable" {
			fmt.Fprintf(out, "evaluate: %s credential (%s) is unusable: %s\n", s.Provider, s.Source, s.reason)
		}
	}
}

func (r resolvedHops) credentialExit() int {
	code := exitUnconfigured
	for _, hop := range r.hops {
		switch hop.loaded.status.State {
		case "unusable":
			return exitCredentialBroken
		case "ok":
			code = exitAnswered
		}
	}
	return code
}

// clients applies the one drop rule. startupLog reports dropped hops for the
// server; call already reported unusable sources and keeps absent ones quiet.
// Session moves still go to log in either entry point.
func (r resolvedHops) clients(startupLog io.Writer) ([]*Client, Config, error) {
	var usable []resolvedHop
	for _, hop := range r.hops {
		if hop.loaded.err == nil {
			usable = append(usable, hop)
		}
	}
	if len(usable) == 0 {
		err := r.hops[0].loaded.err
		for _, hop := range r.hops[1:] {
			err = fmt.Errorf("%w; the %s fallback cannot start either: %v", err,
				hop.config.Provider.Name, hop.loaded.err)
		}
		return nil, r.config, err
	}
	cfg := loadedConfig(usable)
	var clients []*Client
	for _, hop := range usable {
		clients = append(clients, clientForHop(hop))
	}
	r.logDropped(startupLog, usable)

	return clients, cfg, nil
}

// loadedConfig describes only the destinations that survived credential loading.
func loadedConfig(usable []resolvedHop) Config {
	cfg := usable[0].config
	cfg.Fallback, cfg.AdditionalHops = nil, nil
	for i, hop := range usable[1:] {
		if i == 0 {
			cfg.Fallback = &FallbackConfig{Provider: hop.config.Provider, KeyFile: hop.config.KeyFile, KeyFileDefaulted: hop.config.KeyFileDefaulted}
		} else {
			cfg.AdditionalHops = append(cfg.AdditionalHops, hop.config)
		}
	}
	return cfg
}

// logDropped preserves pair diagnostics and logs each unusable later hop once.
func (r resolvedHops) logDropped(out io.Writer, usable []resolvedHop) {
	if len(r.hops) == 2 && len(usable) == 1 {
		if r.hops[0].loaded.err != nil {
			fmt.Fprintf(out, "evaluate: %v; using the %s fallback\n", r.hops[0].loaded.err, usable[0].config.Provider.Name)
		} else {
			fmt.Fprintf(out, "evaluate: the %s fallback is off: %v\n", r.hops[1].config.Provider.Name, r.hops[1].loaded.err)
		}
		return
	}
	for _, hop := range r.hops {
		if hop.loaded.err != nil {
			fmt.Fprintf(out, "evaluate: dropping %s hop: %v\n", hop.config.Provider.Name, hop.loaded.err)
		}
	}
}

func clientForHop(hop resolvedHop) *Client {
	cfg := hop.config
	return &Client{
		Provider: applyOperator(cfg.Provider, cfg.AllowImages, cfg.LongContext),
		Model:    cfg.Model, APIKey: hop.loaded.key, Timeout: cfg.Timeout, HopTimeout: cfg.HopTimeout,
		MaxRetries: cfg.MaxRetries, HTTP: newHTTPClient(), Backoff: time.Second,
	}
}

// Constructor adapters retain the existing single-backend and configured-pair
// entry points; credential loading and selection stay in their owners.
func newClient(cfg Config) (*Client, error) {
	hop := resolvedHop{config: cfg, loaded: loadCredentialSource(cfg, os.LookupEnv)}
	if hop.loaded.err != nil {
		return nil, hop.loaded.err
	}
	return clientForHop(hop), nil
}

func newClients(cfg Config, log io.Writer) (*chainRunner, Config, error) {
	return startChain(resolveConfiguredHops(cfg, os.LookupEnv), log, log)
}

// configuredChainNames serializes setup's resolved order, including later hops.
func configuredChainNames(cfg Config) string {
	var names []string
	for _, hop := range cfg.chainConfigs() {
		names = append(names, hop.Provider.Name)
	}
	return strings.Join(names, ",")
}
