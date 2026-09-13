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
import json
import os
from pathlib import Path
import sys

ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/outputs", "TMPDIR": "/outputs",
               "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}


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


def launch(argv: list[str]) -> None:
    validate_argv(argv)
    restrict_network()
    os.chdir("/inputs")
    # Replace PID 1: Docker observes the workload's exit status, not a mutable
    # result file or a wrapper's claim. stdout/stderr are collected by the host.
    os.execvpe(argv[0], argv, ENVIRONMENT)


if __name__ == "__main__":
    with Path("/__speckit/request.json").open("rb") as request:
        body = request.read(131073)
    if len(body) > 131072:
        raise ValueError("verification request byte limit exceeded")
    value = json.loads(body)
    if not isinstance(value, dict) or set(value) != {"argv"}:
        raise ValueError("invalid immutable verification request")
    launch(value["argv"])
