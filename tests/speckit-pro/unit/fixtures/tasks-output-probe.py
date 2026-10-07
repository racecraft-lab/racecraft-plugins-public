import json
import os
import shutil
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from speckit_pro_runner import atomic_write
from speckit_pro_runner.helpers import tasks_inputs
from speckit_pro_runner.helpers.registry import dispatch_helper


def call(helper, inputs, mode="read_only"):
    request = SimpleNamespace(helper_id=helper, operation=helper, mode=mode,
                              inputs=inputs, request_id=None)
    return dispatch_helper(request)


def setup_project(root):
    (root / ".specify").mkdir()
    feature = root / "specs/example"
    (feature / "checklists").mkdir(parents=True)
    for name in ("spec.md", "plan.md", "checklists/security.md"):
        (feature / name).write_text("Clean planning input.\n")
    return feature


def tasks_brief(root, feature, variant):
    verdict = call("validate-gate", {"gate": "G4", "feature_dir": "specs/example"})["data"]["stdout_json"]
    if variant == "before brief replacement":
        feature.rename(root / "original")
        shutil.copytree(root / "original", feature)
    return call("phase-brief", {"phase": "Tasks", "workflow_file": "docs/workflow.md",
                                 "feature_dir": "specs/example", "g4_judged": verdict["judged"],
                                 "g4_feature_identity": verdict.get("feature_identity")})


def prepare_targets(state, output):
    root = state["root"]
    feature = state["feature"]
    variant = state["variant"]
    outside = state["outside"]
    snapshot = Path(output["snapshot_dir"])
    (snapshot / "tasks.md").write_text("# Tasks\n\n- [ ] T001 Build the feature\n")
    victim = Path(outside).resolve() if "out-root" in variant else root / "victim"
    victim.mkdir(exist_ok=True)
    (victim / "tasks.md").write_text("Victim must stay unchanged\n")
    return {"variant": variant, "root": root, "feature": feature, "snapshot": snapshot,
            "victim": victim, "old": root / "original", "leaf": feature / "tasks.md",
            "fired": [False], "real_open_parent": tasks_inputs.trusted_open_directory,
            "real_replace": os.replace, "real_open": os.open,
            "real_verify": atomic_write.verify_bound_publication,
            "real_response": tasks_inputs.response,
            "real_check": atomic_write.ensure_write_target_matches_snapshot_fd}


def setup_leaf_variant(state):
    variant = state["variant"]
    feature = state["feature"]
    leaf = state["leaf"]
    old = state["old"]
    victim = state["victim"]
    if variant == "parent replacement":
        feature.rename(old)
        feature.mkdir()
    elif variant.startswith("parent symlink"):
        feature.rename(old)
        feature.symlink_to(victim, target_is_directory=True)
    elif variant.startswith("leaf symlink") and "during" not in variant:
        leaf.symlink_to(victim / "tasks.md")
    elif variant == "hard-linked leaf":
        os.link(victim / "tasks.md", leaf)
    elif variant == "fifo leaf":
        os.mkfifo(leaf)
    elif variant == "directory leaf":
        leaf.mkdir()
    elif variant == "existing regular" or "existing:" in variant:
        leaf.write_text("Old tasks\n")
    elif variant == "parent missing":
        feature.rename(old)
    elif variant == "parent file":
        feature.rename(old)
        feature.write_text("Not a directory")


def move_parent(state):
    state["feature"].rename(state["old"])
    state["feature"].symlink_to(state["victim"], target_is_directory=True)


def mutate_output(state, name, parent):
    form = state["variant"].rsplit(":", 1)[1]
    path = state["feature"] / name
    if form == "direct write":
        path.write_text("Injected output")
        return
    if form == "transient hard link":
        alias = state["root"] / "alias"
        os.link(path, alias)
        alias.write_text("Injected output")
        alias.unlink()
        return
    os.unlink(name, dir_fd=parent)
    if form == "regular":
        path.write_text("Injected output")
    elif form == "hard link":
        os.link(state["victim"] / "tasks.md", path)
    elif form.startswith("symlink"):
        path.symlink_to(state["victim"] / "tasks.md")
    elif form == "fifo":
        os.mkfifo(path)


def acquire(state, *args, **kwargs):
    value = state["real_open_parent"](*args, **kwargs)
    if not state["fired"][0]:
        state["fired"][0] = True
        move_parent(state)
    return value


def replace_after_move(state, *args, **kwargs):
    state["fired"][0] = True
    move_parent(state)
    return state["real_replace"](*args, **kwargs)


def create_temp(state, path, flags, *args, **kwargs):
    value = state["real_open"](path, flags, *args, **kwargs)
    if flags & os.O_CREAT and not state["fired"][0]:
        state["fired"][0] = True
        variant = state["variant"]
        if variant.startswith("parent during temp"):
            move_parent(state)
        elif variant == "hard link during temp":
            os.link(state["victim"] / "tasks.md", state["leaf"])
        else:
            state["leaf"].symlink_to(state["victim"] / "tasks.md")
    return value


def replace_mutated(state, source, target, **kwargs):
    state["fired"][0] = True
    if state["variant"].startswith("temp during rename:"):
        mutate_output(state, source, kwargs["src_dir_fd"])
    value = state["real_replace"](source, target, **kwargs)
    if state["variant"].startswith("output during rename:"):
        mutate_output(state, target, kwargs["dst_dir_fd"])
    return value


def check_mutated(state, parent, target, expected):
    value = state["real_check"](parent, target, expected)
    state["fired"][0] = True
    name = next(path.name for path in state["feature"].glob(".tasks.md.tmp-*"))
    mutate_output(state, name, parent)
    return value


def verify_mutated(state, binding, held_fd, name, content, installed=False):
    window = state["variant"].split(":", 1)[0]
    selected = installed == window.startswith("output")
    if selected and "before check" in window:
        mutate_output(state, name, binding.parent_fd)
        state["fired"][0] = True
    value = state["real_verify"](binding, held_fd, name, content, installed=installed)
    if selected and "after check" in window:
        mutate_output(state, name, binding.parent_fd)
        state["fired"][0] = True
    return value


def response_mutated(state, *args, **kwargs):
    with ExitStack() as stack:
        parent = os.open(state["feature"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, parent)
        mutate_output(state, "tasks.md", parent)
    state["fired"][0] = True
    return state["real_response"](*args, **kwargs)


def install_hooks(stack, state):
    variant = state["variant"]
    if variant.startswith("output at response:"):
        hook = lambda *args, **kwargs: response_mutated(state, *args, **kwargs)
        stack.enter_context(patch.object(tasks_inputs, "response", hook))
    if variant.startswith(("temp before check", "temp after check", "output before check", "output after check")):
        hook = lambda *args, **kwargs: verify_mutated(state, *args, **kwargs)
        stack.enter_context(patch.object(atomic_write, "verify_bound_publication", hook))
    if variant.startswith(("temp during rename:", "output during rename:")):
        hook = lambda *args, **kwargs: replace_mutated(state, *args, **kwargs)
        stack.enter_context(patch.object(os, "replace", hook))
    if variant.startswith("temp during check:"):
        hook = lambda *args: check_mutated(state, *args)
        stack.enter_context(patch.object(atomic_write, "ensure_write_target_matches_snapshot_fd", hook))
    if variant == "parent during acquisition":
        hook = lambda *args, **kwargs: acquire(state, *args, **kwargs)
        stack.enter_context(patch.object(tasks_inputs, "trusted_open_directory", hook))
    if variant == "parent during rename out-root":
        hook = lambda *args, **kwargs: replace_after_move(state, *args, **kwargs)
        stack.enter_context(patch.object(os, "replace", hook))
    if "during temp" in variant:
        hook = lambda path, flags, *args, **kwargs: create_temp(state, path, flags, *args, **kwargs)
        stack.enter_context(patch.object(os, "open", hook))


def publish(state, output):
    with ExitStack() as stack:
        install_hooks(stack, state)
        result = call("publish-tasks-output", output, "apply")
    if "during" in state["variant"] or "check" in state["variant"] or "at response" in state["variant"]:
        assert state["fired"][0], "fault was not exercised"
    return result


def report(state, brief, result):
    variant = state["variant"]
    tree = state["old"] if state["old"].exists() else state["feature"]
    entries = [] if variant == "parent file" else sorted(path.name for path in tree.iterdir())
    published = state["leaf"].read_text() if variant in ("clean", "existing regular") and state["leaf"].exists() else None
    return {"result": result, "victim": (state["victim"] / "tasks.md").read_text(),
            "published": published, "deferred_hooks": brief["data"]["inputs"].get("defer_after_hooks", False),
            "entries": entries}


def main():
    variant = sys.argv[1]
    with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
        root = Path(directory).resolve()
        os.chdir(root)
        feature = setup_project(root)
        brief = tasks_brief(root, feature, variant)
        if variant == "before brief replacement":
            print(json.dumps({"result": brief, "victim": "Victim must stay unchanged\n",
                              "published": None, "entries": []}))
            return
        assert brief["status"] == "ok", brief
        output = brief["data"]["inputs"]["tasks_output"]
        state = prepare_targets({"root": root, "outside": outside, "feature": feature,
                                 "variant": variant}, output)
        setup_leaf_variant(state)
        try:
            result = publish(state, output)
            print(json.dumps(report(state, brief, result)))
        finally:
            shutil.rmtree(state["snapshot"], ignore_errors=True)


if __name__ == "__main__":
    main()
