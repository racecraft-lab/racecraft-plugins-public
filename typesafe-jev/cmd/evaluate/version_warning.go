package main

import (
	"fmt"
	"os"
)

// pluginVersionNote reports the same startup warning to the client and stderr.
func pluginVersionNote() string {
	plugin := os.Getenv("EVALUATE_PLUGIN_VERSION")
	if plugin == "" || plugin == version {
		return ""
	}
	detail := fmt.Sprintf("evaluate binary version %s differs from plugin version %s", version, plugin)
	if version == "dev" {
		detail = fmt.Sprintf("evaluate binary version dev is a dev build; plugin version is %s", plugin)
	}
	warning := "Warning: " + detail + "; rerun the plugin's installer: python3 scripts/install_evaluate.py --force (from the plugin directory)."
	fmt.Fprintln(os.Stderr, warning)
	return "\n" + warning
}
