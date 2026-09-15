"""Trusted image entrypoint; no imports from the workload and no host execution.

Docker's default seccomp policy stays installed. This additional Linux/aarch64
filter denies socket operations (including loopback/Unix sockets) and io_uring.
It is one layer, not a standalone sandbox or evidence qualification authority.
Source: https://docs.kernel.org/userspace-api/seccomp_filter.html
Numbers: Linux v6.12 include/uapi/{asm-generic/unistd.h,linux/{audit,seccomp}.h}.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys

ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/outputs", "TMPDIR": "/outputs",
               "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
QUALIFIED_ENVIRONMENT = {**ENVIRONMENT, "PYTHONNOUSERSITE": "1", "XDG_CONFIG_HOME": "/outputs",
                         "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
                         "GIT_CONFIG_COUNT": "0", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}
RUNTIME_PREFIX = b"SPECKIT_DOCKER_RUNTIME_V2 "
INJECTED_FILE_SHA256 = {
    "/etc/hostname": "cfff937c5527d1a5015678272f2ea68453aac0a4fdbfdf4cbcc60e193b4c63be",
    "/etc/hosts": "ba0a20158b52d3a04aecb4882f66ea5f6b1074a292c5102baae85f8d74ec0580",
    "/etc/resolv.conf": "6b6f74dd21057f8024dfadde96392cf10caebe30974ad36af83917b32e4f351e",
}


class _Instruction(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]


class _Program(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("instructions", ctypes.POINTER(_Instruction))]


def validate_argv(argv: object) -> list[str]:
    if not isinstance(argv, list) or not 1 <= len(argv) <= 256:
        raise ValueError("verification requires a bounded direct argument vector")
    if any(not isinstance(arg, str) or "\x00" in arg for arg in argv) or not argv[0]:
        raise ValueError("verification arguments must be strings without NUL")
    if sum(len(arg.encode("utf-8")) for arg in argv) > 65536:
        raise ValueError("verification argument byte limit exceeded")
    return argv


def filter_instructions() -> list[tuple[int, int, int, int]]:
    # Load arch, kill an ABI mismatch, then inspect syscall number. Always allow
    # only after every deny check; child fork/exec inherits the stacked filter.
    instructions = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xC00000B7),
                    (0x06, 0, 0, 0x80000000), (0x20, 0, 0, 0)]
    for number in (*range(198, 213), 242, 243, 269, 425, 426, 427):
        instructions.extend([(0x15, 0, 1, number), (0x06, 0, 0, 0x00050000 | errno.EPERM)])
    return [*instructions, (0x06, 0, 0, 0x7FFF0000)]


def restrict_network() -> None:
    if sys.platform != "linux" or os.uname().machine != "aarch64" or sys.byteorder != "little":
        raise ValueError("verification filter requires Linux little-endian aarch64")
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines())
    if (status.get("Threads", "").strip() != "1" or status.get("Seccomp", "").strip() != "2"
            or int(status.get("Seccomp_filters", "0")) < 1 or int(status.get("CapEff", "1"), 16) != 0
            or status.get("NoNewPrivs", "").strip() != "1" or os.getuid() != 65532):
        raise ValueError("verification launcher is missing required container restrictions")
    instructions = filter_instructions()
    storage = (_Instruction * len(instructions))(*(_Instruction(*item) for item in instructions))
    program = _Program(len(instructions), storage)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes, libc.prctl.restype = [ctypes.c_int], ctypes.c_int
    if libc.prctl(38, ctypes.c_ulong(1), ctypes.c_ulong(0), ctypes.c_ulong(0), ctypes.c_ulong(0)):
        raise OSError(ctypes.get_errno(), "setting no-new-privileges failed")
    if libc.prctl(22, ctypes.c_ulong(2), ctypes.byref(program), ctypes.c_ulong(0), ctypes.c_ulong(0)):
        raise OSError(ctypes.get_errno(), "installing additive seccomp filter failed")


def _file_sha256(path: str) -> str:
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _injected_file_attestation() -> dict[str, dict[str, object]]:
    observed = {}
    for path, expected_sha256 in INJECTED_FILE_SHA256.items():
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            body = stream.read(65537)
            after = os.fstat(stream.fileno())
        identity = lambda info: (info.st_dev, info.st_ino, info.st_mode, info.st_size,
                                 info.st_mtime_ns, info.st_ctime_ns)
        actual_sha256 = hashlib.sha256(body).hexdigest()
        if (not stat.S_ISREG(before.st_mode) or len(body) > 65536 or identity(before) != identity(after)
                or actual_sha256 != expected_sha256 or os.access(path, os.W_OK)):
            raise ValueError(f"qualified Docker injected file disagrees: {path}")
        observed[path] = {"sha256": actual_sha256, "writable": False}
    return observed


def runtime_attestation(argv: list[str]) -> dict[str, object]:
    """Describe the injected PID 1 and exact executable from inside confinement."""
    executable = shutil.which(argv[0], path=QUALIFIED_ENVIRONMENT["PATH"])
    if executable is None or not os.path.isabs(executable):
        raise ValueError("workload executable is not resolvable in the qualified image")
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines())
    init_path = os.readlink("/proc/1/exe")
    cmdline = Path("/proc/1/cmdline").read_bytes()
    if os.getpid() == 1 or not cmdline or len(cmdline) > 4096:
        raise ValueError("qualified execution requires a bounded injected init process")
    confinement = {"uid": os.getuid(), "gid": os.getgid(), "threads": status.get("Threads", "").strip(),
                   "seccomp": status.get("Seccomp", "").strip(),
                   "seccomp_filters": status.get("Seccomp_filters", "").strip(),
                   "cap_eff": status.get("CapEff", "").strip(), "no_new_privs": status.get("NoNewPrivs", "").strip()}
    if (confinement["uid"], confinement["gid"], confinement["threads"], confinement["seccomp"],
            confinement["cap_eff"], confinement["no_new_privs"]) != (65532, 65532, "1", "2", "0000000000000000", "1"):
        raise ValueError("qualified runtime attestation observed weakened confinement")
    if int(str(confinement["seccomp_filters"])) < 2:
        raise ValueError("qualified runtime attestation did not observe the additive filter")
    return {"schema_version": "docker-launcher-runtime/v2", "launcher_pid": os.getpid(),
            "init": {"pid": 1, "path": init_path, "sha256": _file_sha256("/proc/1/exe"),
                     "cmdline_sha256": hashlib.sha256(cmdline).hexdigest()},
            "workload_executable": {"path": os.path.realpath(executable), "sha256": _file_sha256(executable)},
            "confinement": confinement, "injected_files": _injected_file_attestation()}


def runtime_frame(argv: list[str]) -> bytes:
    payload = json.dumps(runtime_attestation(argv), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(payload) > 8192:
        raise ValueError("runtime attestation exceeds the frame limit")
    return RUNTIME_PREFIX + str(len(payload)).encode("ascii") + b" " + hashlib.sha256(payload).hexdigest().encode("ascii") + b"\n" + payload + b"\n"


def launch(argv: list[str], *, qualified: bool = False) -> None:
    validate_argv(argv)
    restrict_network()
    os.chdir("/inputs")
    if qualified:
        os.write(1, runtime_frame(argv))
    # Replace the init process's child so Docker observes the workload's exit.
    os.execvpe(argv[0], argv, QUALIFIED_ENVIRONMENT if qualified else ENVIRONMENT)


if __name__ == "__main__":
    with Path("/__speckit/request.json").open("rb") as request:
        body = request.read(131073)
    if len(body) > 131072:
        raise ValueError("verification request byte limit exceeded")
    value = json.loads(body)
    if (not isinstance(value, dict) or set(value) not in ({"argv"}, {"argv", "qualification_profile"})
            or value.get("qualification_profile") not in (None, "docker-qualified/v2")):
        raise ValueError("invalid immutable verification request")
    launch(value["argv"], qualified=value.get("qualification_profile") == "docker-qualified/v2")
