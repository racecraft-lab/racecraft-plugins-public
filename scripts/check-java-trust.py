#!/usr/bin/env python3
"""Check or surgically remove incident roots from the selected JDK cacerts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

# SHA-256 of the complete DER certificate, independent of vendor alias names.
BLOCKED_SHA256 = frozenset({
    "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b",  # emSign ECC G3
    "d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4",  # AAA Certificate Services
})


def keytool(java_home: Path, store: Path, *arguments: str) -> str:
    return subprocess.run(
        [str(java_home / "bin/keytool"), *arguments, "-keystore", str(store),
         "-storepass", "changeit", "-J-Duser.language=en", "-J-Duser.country=US"],
        check=True, shell=False, capture_output=True, text=True, encoding="utf-8", timeout=60,
    ).stdout


def parse_inventory(listing: str) -> dict[str, str]:
    count = re.search(r"(?m)^Your keystore contains (\d+) entr(?:y|ies)\s*$", listing)
    entries = re.split(r"(?m)^Alias name: ", listing)[1:]
    if count is None or int(count[1]) != len(entries) or not entries:
        raise ValueError("Cannot establish a complete, nonempty Java trust inventory")
    inventory: dict[str, str] = {}
    for entry in entries:
        alias, _, body = entry.partition("\n")
        certificates = re.findall(r"-----BEGIN CERTIFICATE-----\s*([A-Za-z0-9+/=\s]+?)\s*-----END CERTIFICATE-----", body)
        if not alias or alias in inventory or "Entry type: trustedCertEntry\n" not in body or len(certificates) != 1:
            raise ValueError("Unexpected Java trust entry or certificate chain")
        der = base64.b64decode("".join(certificates[0].split()), validate=True)
        inventory[alias] = hashlib.sha256(der).hexdigest()
    if listing.count("-----BEGIN CERTIFICATE-----") != len(inventory):
        raise ValueError("Unaccounted certificate in Java trust inventory")
    return inventory


def inventory(java_home: Path, store: Path) -> dict[str, str]:
    return parse_inventory(keytool(java_home, store, "-list", "-rfc"))


def require_preserved_roots(before: dict[str, str], after: dict[str, str]) -> None:
    expected = {alias: digest for alias, digest in before.items() if digest not in BLOCKED_SHA256}
    if not expected or after != expected:
        raise ValueError("Blocked roots remain or unrelated Java trust entries changed")


def check_trust(java_home: Path, remove_blocked: bool) -> None:
    security = java_home / "lib/security"
    if (security / "jssecacerts").exists() or any(
        "javax.net.ssl.trustStore" in os.environ.get(name, "")
        for name in ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS")
    ):
        raise ValueError("Alternate Java trust store would bypass the selected cacerts")
    store = (security / "cacerts").resolve(strict=True)
    before = inventory(java_home, store)
    blocked = [alias for alias, digest in before.items() if digest in BLOCKED_SHA256]
    if blocked and remove_blocked:
        with tempfile.TemporaryDirectory(prefix="java-cacerts-", dir=store.parent) as temporary:
            staged = Path(temporary) / "cacerts"
            shutil.copy2(store, staged)
            for alias in blocked:
                keytool(java_home, staged, "-delete", "-alias", alias)
            require_preserved_roots(before, inventory(java_home, staged))
            if inventory(java_home, store) != before:
                raise ValueError("Java trust store changed during verification")
            staged.replace(store)
    require_preserved_roots(before, inventory(java_home, store))
    print(f"Java trust verified: {len(before) - len(blocked)} preserved roots; incident roots absent")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java-home", type=Path, default=os.environ.get("JAVA_HOME"))
    parser.add_argument("--remove-blocked", action="store_true")
    args = parser.parse_args()
    if args.java_home is None:
        parser.error("JAVA_HOME or --java-home is required")
    check_trust(args.java_home, args.remove_blocked)


if __name__ == "__main__":
    main()
