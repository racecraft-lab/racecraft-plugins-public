# Sourced by each case's scaffold.sh.
#
# Every run gets its own HOME, and bin/evaluate-launch resolves both the binary
# and the key file under $HOME. Without these links the server exits before the
# client speaks to it, and the run reads as "the model chose not to use the
# tool" when nothing was ever offered.
#
# Symlinks, not copies: the key stays in one place on disk, and readKeyFile's
# permission check follows to the real file's own mode.

# operator_home prints the home directory of the account running the eval.
# HOME cannot answer this: it has already been redirected at the run's
# temporary directory, so reading it would be circular.
#
# The passwd database is consulted directly rather than expanding ~user through
# eval. eval would re-parse the username as shell source, and the two queries
# below cover Linux and macOS between them without that.
operator_home() {
	user=$(id -un) || return 1
	home=$(getent passwd "$user" 2>/dev/null | cut -d: -f6)
	if [ -z "$home" ]; then
		home=$(dscl . -read "/Users/$user" NFSHomeDirectory 2>/dev/null | sed 's/^NFSHomeDirectory: //')
	fi
	[ -n "$home" ] && [ -d "$home" ] || return 1
	printf '%s\n' "$home"
}

link_evaluate_server() {
	real_home=$(operator_home) || {
		echo "scaffold: cannot determine the operator's home directory for $(id -un)" >&2
		echo "scaffold: the eval cannot reach the evaluate binary without it" >&2
		return 1
	}

	# Required. Missing, the server exits at startup and every case in the run
	# reports the tool as unused, which is indistinguishable from the model
	# declining to call it. Fail here instead, where the cause is visible.
	binary="$real_home/.local/libexec/racecraft-jev/evaluate"
	if [ ! -x "$binary" ]; then
		echo "scaffold: no evaluate binary at $binary" >&2
		echo "scaffold: run 'task install', or 'sh install.sh' for a release build" >&2
		return 1
	fi
	mkdir -p "$HOME/.local/libexec/racecraft-jev"
	ln -sf "$binary" "$HOME/.local/libexec/racecraft-jev/evaluate"

	# Optional: an operator may supply the credential through the provider's
	# environment variable instead of a key file. The server reports a missing
	# credential clearly on its own, so this one does not fail the scaffold.
	key="$real_home/.config/racecraft-jev/openrouter.key"
	if [ -f "$key" ]; then
		mkdir -p "$HOME/.config/racecraft-jev"
		ln -sf "$key" "$HOME/.config/racecraft-jev/openrouter.key"
	else
		echo "scaffold: no key file at $key; relying on the provider's environment variable" >&2
	fi
}
