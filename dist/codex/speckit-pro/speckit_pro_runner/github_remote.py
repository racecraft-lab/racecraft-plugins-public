"""The one home for the GitHub.com remote URL spellings that name an owner/name repository.

Callers read the remote URL themselves; this module only says which spellings name the repository.
"""

from __future__ import annotations

HTTPS = "https://github.com/"
SCP = "git@github.com:"
SSH = "ssh://git@github.com/"
PREFIXES = (HTTPS, SCP, SSH)
SUFFIXES = ("", ".git")
ALL_FORMS = tuple((prefix, suffix) for prefix in PREFIXES for suffix in SUFFIXES)
# The qualified gh-stack profile accepts this narrower subset: no bare scp spelling and no ssh:// URL.
GH_STACK_FORMS = ((HTTPS, ""), (HTTPS, ".git"), (SCP, ".git"))


def remote_urls(repository: str, forms: tuple[tuple[str, str], ...] = ALL_FORMS) -> frozenset[str]:
    """Every remote URL, in the given spellings, that names this owner/name on GitHub.com."""
    return frozenset(f"{prefix}{repository}{suffix}" for prefix, suffix in forms)
