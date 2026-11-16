package main

// config.go owns backend rows and setting validation. Runtime resolution lives
// here because it composes those settings with credentials and client startup;
// putting that work in the backend-spec owner would mix data with runtime state.

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
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

// resolveHops returns today's ordered list (at most two hops), including the
// verdict for an unusable hop so --check can remain stricter than the server.
func resolveHops(look lookupFunc, pluginDefaults bool) (resolvedHops, error) {
	cfg, err := resolveHopConfig(look, pluginDefaults)
	if err != nil {
		return resolvedHops{}, err
	}
	return resolveConfiguredHops(cfg, look), nil
}

func resolveConfiguredHops(cfg Config, look lookupFunc) resolvedHops {
	r := resolvedHops{config: cfg}
	configs := []Config{cfg}
	if cfg.Fallback != nil {
		configs = append(configs, cfg.fallbackConfig())
	}
	for _, hop := range configs {
		r.hops = append(r.hops, resolvedHop{config: hop, loaded: loadCredentialSource(hop, look)})
	}
	return r
}

func resolveConfig(look lookupFunc) (Config, error) {
	return resolveHopConfig(look, false)
}

func resolveCallConfig(look lookupFunc, pluginDefaults bool) (Config, error) {
	return resolveHopConfig(look, pluginDefaults)
}

// resolveHopConfig is the configuration policy shared by setup and runtime.
// Setup deliberately resolves settings without opening any credential file.
func resolveHopConfig(look lookupFunc, pluginDefaults bool) (Config, error) {
	var cfg Config
	home := ""
	if pluginDefaults {
		home = homeDir(look)
	}

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
// diagnostics stable when more than one setting is invalid.
func resolveHopKeyFile(look lookupFunc, name, provider, home string) (string, bool, error) {
	path, err := resolveKeyFileVar(look, name)
	if err != nil || path != "" || home == "" {
		return path, false, err
	}
	candidate := filepath.Join(home, filepath.FromSlash(pluginKeyDirectory), provider+".key")
	if _, err := os.Lstat(candidate); err != nil {
		return "", false, nil
	}
	path, err = resolveKeyFileVar(func(string) (string, bool) { return candidate, true }, name)
	return path, true, err
}

// sources preserves call's two-source report while resolution owns the list.
func (r resolvedHops) sources() (sourceStatus, *sourceStatus) {
	primary := r.hops[0].loaded.status
	if len(r.hops) == 1 {
		return primary, nil
	}
	fallback := r.hops[1].loaded.status
	return primary, &fallback
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
func (r resolvedHops) clients(log, startupLog io.Writer) (*Client, Config, error) {
	var usable []resolvedHop
	for _, hop := range r.hops {
		if hop.loaded.err == nil {
			usable = append(usable, hop)
		}
	}
	if len(usable) == 0 {
		err := r.hops[0].loaded.err
		if len(r.hops) == 2 {
			err = fmt.Errorf("%w; the %s fallback cannot start either: %v", err,
				r.hops[1].config.Provider.Name, r.hops[1].loaded.err)
		}
		return nil, r.config, err
	}
	cfg := usable[0].config
	client := clientForHop(usable[0])
	if len(usable) == 2 {
		client.Fallback = clientForHop(usable[1])
		client.Log = log
	} else {
		cfg.Fallback = nil
		if len(r.hops) == 2 {
			if r.hops[0].loaded.err != nil {
				fmt.Fprintf(startupLog, "evaluate: %v; using the %s fallback\n", r.hops[0].loaded.err, cfg.Provider.Name)
			} else {
				fmt.Fprintf(startupLog, "evaluate: the %s fallback is off: %v\n", r.hops[1].config.Provider.Name, r.hops[1].loaded.err)
			}
		}
	}
	return client, cfg, nil
}

func clientForHop(hop resolvedHop) *Client {
	cfg := hop.config
	return &Client{
		Provider: applyOperator(cfg.Provider, cfg.AllowImages, cfg.LongContext),
		Model:    cfg.Model, APIKey: hop.loaded.key, Timeout: cfg.Timeout,
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

func newClients(cfg Config, log io.Writer) (*Client, Config, error) {
	return resolveConfiguredHops(cfg, os.LookupEnv).clients(log, log)
}
