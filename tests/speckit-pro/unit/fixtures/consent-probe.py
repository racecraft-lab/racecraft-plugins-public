import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from speckit_pro_runner.helpers.registry import dispatch_helper


def setup_case(case, directory):
    root = Path(directory) / "project"
    root.mkdir()
    parent = root / ".specify"
    parent.mkdir()
    target = parent / "extensions.yml"
    target.write_text(case["text"], encoding="utf-8")
    topology = case.get("topology", "regular")
    replacement = Path(directory) / "replacement.yml"
    replacement.write_text(case.get("replacement", case["text"]), encoding="utf-8")
    if topology == "pre_open":
        replacement.replace(target)
    elif topology == "hard_link":
        target.unlink()
        os.link(replacement, target)
    elif topology == "final_symlink":
        target.unlink()
        target.symlink_to(replacement)
    elif topology == "directory_symlink":
        parent.rename(root / "held")
        parent.symlink_to(root / "held", target_is_directory=True)
    return root, parent, target, replacement, topology


def phase_inputs(case, root):
    inputs = {"phase": case["phase"], "workflow_file": "docs/workflow.md",
              "feature_dir": "specs/example"}
    if case["phase"] == "Tasks":
        import hashlib
        feature = root / "specs/example"
        (feature / "checklists").mkdir(parents=True)
        info = feature.stat()
        inputs["g4_feature_identity"] = {"device": info.st_dev, "inode": info.st_ino}
        inputs["g4_judged"] = {}
        for name in ("spec.md", "plan.md", "checklists/security.md"):
            (feature / name).write_bytes(b"clean fixture\n")
            inputs["g4_judged"][name] = hashlib.sha256(b"clean fixture\n").hexdigest()
    return inputs


def dispatch_case(case, root, opened, fired):
    previous = Path.cwd()
    os.chdir(root)
    try:
        with patch.object(os, "open", opened):
            request = SimpleNamespace(helper_id="phase-brief", operation="phase-brief",
                                      mode="read_only", request_id=None,
                                      inputs=phase_inputs(case, root))
            report = dispatch_helper(request)
        return {"result": report, "opened": bool(fired)}
    finally:
        os.chdir(previous)


def run_case(case):
    with tempfile.TemporaryDirectory() as directory:
        root, parent, target, replacement, topology = setup_case(case, directory)
        fired = []
        original_open = os.open

        def opened(path, flags, *args, **kwargs):
            fd = original_open(path, flags, *args, **kwargs)
            if path == "extensions.yml" and not fired:
                fired.append(True)
                if topology == "post_open":
                    replacement.replace(target)
                elif topology == "post_directory":
                    parent.rename(root / "held")
                    parent.mkdir()
                    replacement.replace(target)
            return fd

        return dispatch_case(case, root, opened, fired)


def main():
    print(json.dumps([run_case(case) for case in json.load(sys.stdin)]))


if __name__ == "__main__":
    main()
