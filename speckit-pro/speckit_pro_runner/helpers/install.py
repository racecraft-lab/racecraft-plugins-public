"""Codex agent install: plan, apply and roll back the agent TOML files under an anchored, no-clobber directory.

The doctor helpers, route policy, capability probe and runner-invocation gate live in their own modules.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import re
import secrets
import stat
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..agent_materialization import materialize_agent_policy
from ..agent_inventory import CODEX_REQUIRED_AGENT_NAMES
from ..envelope import diagnostic, is_diagnostic, response
from ..trusted_io import find_repo_root
from .mutation import empty_mutation, operation_record
from .codex_capabilities import (
    capture_codex_runtime_capabilities,
    normalize_codex_runtime_capability_snapshot,
)
from .install_doctor import run_doctor_helper
from .route_policy import (
    CODEX_LUNA_FALLBACK_MODEL,
    CODEX_LUNA_SOURCE_MODEL,
    CODEX_OPTIONAL_HELPER_NAME,
    CODEX_SOL_SOURCE_MODEL,
    CODEX_SOURCE_AGENT_POLICIES,
    CODEX_SOURCE_AGENT_TOML_NAMES as CODEX_SOURCE_AGENT_TOML_NAMES,
    SUPPORTED_CODEX_AGENT_MODELS,
    codex_agent_source_roster,
    codex_plugin_root,
    load_codex_route_policy_manifest,
    route_policy_digest,
)

CODEX_AGENT_STATE_UNSET = object()
CODEX_AGENT_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
CODEX_AGENT_UNLINK_SUPPORTS_DIR_FD = os.unlink in os.supports_dir_fd
WINDOWS_GENERIC_READ = 0x80000000
WINDOWS_GENERIC_WRITE = 0x40000000
WINDOWS_DELETE = 0x00010000
WINDOWS_FILE_WRITE_ATTRIBUTES = 0x00000100
WINDOWS_SYNCHRONIZE = 0x00100000
WINDOWS_FILE_READ_ATTRIBUTES = 0x00000080
WINDOWS_FILE_SHARE_READ = 0x00000001
WINDOWS_FILE_SHARE_WRITE = 0x00000002
WINDOWS_FILE_SHARE_DELETE = 0x00000004
WINDOWS_CREATE_NEW = 1
WINDOWS_OPEN_EXISTING = 3
WINDOWS_FILE_ATTRIBUTE_READONLY = 0x00000001
WINDOWS_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
WINDOWS_FILE_ATTRIBUTE_NORMAL = 0x00000080
WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
WINDOWS_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
WINDOWS_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
WINDOWS_FILE_BASIC_INFO_CLASS = 0
WINDOWS_FILE_DISPOSITION_INFO_CLASS = 4
WINDOWS_FILE_RENAME_INFO_CLASS = 3
WINDOWS_FILE_BEGIN = 0
WINDOWS_ERROR_FILE_NOT_FOUND = 2
WINDOWS_ERROR_PATH_NOT_FOUND = 3
WINDOWS_ERROR_ACCESS_DENIED = 5
WINDOWS_ERROR_INVALID_HANDLE = 6
WINDOWS_ERROR_FILE_EXISTS = 80
WINDOWS_ERROR_ALREADY_EXISTS = 183
WINDOWS_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class _WindowsFileTime(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", ctypes.c_uint32),
        ("dwHighDateTime", ctypes.c_uint32),
    ]


class _WindowsByHandleFileInformation(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", ctypes.c_uint32),
        ("ftCreationTime", _WindowsFileTime),
        ("ftLastAccessTime", _WindowsFileTime),
        ("ftLastWriteTime", _WindowsFileTime),
        ("dwVolumeSerialNumber", ctypes.c_uint32),
        ("nFileSizeHigh", ctypes.c_uint32),
        ("nFileSizeLow", ctypes.c_uint32),
        ("nNumberOfLinks", ctypes.c_uint32),
        ("nFileIndexHigh", ctypes.c_uint32),
        ("nFileIndexLow", ctypes.c_uint32),
    ]


class _WindowsFileRenameInfoHeader(ctypes.Structure):
    _fields_ = [
        ("ReplaceIfExists", ctypes.c_int),
        ("RootDirectory", ctypes.c_void_p),
        ("FileNameLength", ctypes.c_uint32),
    ]


class _WindowsFileBasicInfo(ctypes.Structure):
    _fields_ = [
        ("CreationTime", ctypes.c_longlong),
        ("LastAccessTime", ctypes.c_longlong),
        ("LastWriteTime", ctypes.c_longlong),
        ("ChangeTime", ctypes.c_longlong),
        ("FileAttributes", ctypes.c_uint32),
    ]


class _WindowsFileDispositionInfo(ctypes.Structure):
    _fields_ = [("DeleteFile", ctypes.c_ubyte)]


WINDOWS_FILE_RENAME_INFO_FILENAME_OFFSET = (
    _WindowsFileRenameInfoHeader.FileNameLength.offset + ctypes.sizeof(ctypes.c_uint32)
)


@dataclass(frozen=True)
class CodexAgentFileState:
    content: bytes
    mode: int
    device: int
    inode: int


@dataclass
class CodexAgentCleanupResult:
    public_conflicts: list[str] = field(default_factory=list)
    preserved_private_paths: list[str] = field(default_factory=list)
    cleanup_errors: list[dict[str, str]] = field(default_factory=list)

    @property
    def preserved_paths(self) -> list[str]:
        return list(dict.fromkeys([*self.public_conflicts, *self.preserved_private_paths]))

    def __bool__(self) -> bool:
        return bool(self.public_conflicts or self.preserved_private_paths or self.cleanup_errors)

    def __iter__(self) -> Any:
        return iter(self.preserved_paths)

    def __len__(self) -> int:
        return len(self.preserved_paths)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, list):
            return self.preserved_paths == other
        return super().__eq__(other)


class CodexAgentNoClobberConflict(OSError):
    def __init__(
        self,
        message: str,
        preserved_paths: list[str],
        cleanup_errors: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.preserved_paths = preserved_paths
        self.cleanup_errors = cleanup_errors or []


class CodexAgentWindowsRenameFailure(OSError):
    def __init__(
        self,
        source_name: str,
        target_name: str,
        primary_error: OSError | None,
        close_error: OSError | None,
        outcome: str,
    ) -> None:
        message_error = primary_error if primary_error is not None else close_error
        super().__init__(str(message_error) if message_error is not None else "Windows rename failed")
        self.source_name = source_name
        self.target_name = target_name
        self.primary_error = primary_error
        self.close_error = close_error
        self.outcome = outcome


class CodexAgentWindowsRenameCommittedCloseFailure(CodexAgentWindowsRenameFailure):
    def __init__(self, source_name: str, target_name: str, close_error: OSError) -> None:
        super().__init__(source_name, target_name, None, close_error, "committed")


class CodexAgentRecoveryCopyFailure(OSError):
    def __init__(self, message: str, failed_paths: list[str], preserved_paths: list[str]) -> None:
        super().__init__(message)
        self.failed_paths = failed_paths
        self.preserved_paths = preserved_paths


CODEX_AGENT_PRESERVED_PATH_PROVENANCE_KINDS = {
    "preserved_cleanup_entry",
    "preserved_concurrent_file",
}


def codex_agent_unproven_preserved_path_records(
    preserved_paths: list[str],
    cleanup_errors: list[dict[str, Any]],
    error: str,
) -> list[dict[str, str]]:
    proven_targets = {
        str(cleanup_error["target"])
        for cleanup_error in cleanup_errors
        if cleanup_error.get("kind") in CODEX_AGENT_PRESERVED_PATH_PROVENANCE_KINDS
        and isinstance(cleanup_error.get("target"), str)
    }
    return [
        {
            "kind": "preserved_concurrent_file",
            "target": path,
            "error": error,
        }
        for path in preserved_paths
        if path not in proven_targets
    ]


def codex_agent_windows_kernel32() -> Any:
    windll = getattr(ctypes, "WinDLL", None)
    if not callable(windll):
        raise OSError(errno.ENOTSUP, "Windows ctypes WinDLL is unavailable")
    return windll("kernel32", use_last_error=True)


def codex_agent_windows_last_error() -> int:
    getter = getattr(ctypes, "get_last_error", None)
    if callable(getter):
        return int(getter())
    return int(ctypes.get_errno())


def codex_agent_windows_os_error(operation: str, path: Path | str | None = None) -> OSError:
    error_number = codex_agent_windows_last_error()
    text_path = None if path is None else str(path)
    if error_number in {WINDOWS_ERROR_FILE_EXISTS, WINDOWS_ERROR_ALREADY_EXISTS}:
        return FileExistsError(error_number, operation, text_path)
    if error_number in {WINDOWS_ERROR_FILE_NOT_FOUND, WINDOWS_ERROR_PATH_NOT_FOUND}:
        return FileNotFoundError(error_number, operation, text_path)
    if error_number == WINDOWS_ERROR_ACCESS_DENIED:
        return PermissionError(error_number, operation, text_path)
    return OSError(error_number, f"{operation} failed with Win32 error {error_number}", text_path)


def codex_agent_windows_set_signature(function: Any, argtypes: list[Any], restype: Any) -> None:
    try:
        function.argtypes = argtypes
        function.restype = restype
    except AttributeError:
        pass


def codex_agent_windows_handle_value(raw_handle: Any) -> int:
    if isinstance(raw_handle, ctypes.c_void_p):
        return int(raw_handle.value or 0)
    return int(raw_handle)


def codex_agent_windows_create_file(
    path: Path,
    desired_access: int,
    share_mode: int,
    creation_disposition: int,
    flags_and_attributes: int,
) -> int:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.CreateFileW
    codex_agent_windows_set_signature(
        function,
        [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ],
        ctypes.c_void_p,
    )
    handle = codex_agent_windows_handle_value(
        function(
            str(path),
            desired_access,
            share_mode,
            None,
            creation_disposition,
            flags_and_attributes,
            None,
        )
    )
    if handle == WINDOWS_INVALID_HANDLE_VALUE or handle == 0:
        raise codex_agent_windows_os_error("CreateFileW", path)
    return handle


def codex_agent_windows_close_handle(handle: int) -> OSError | None:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.CloseHandle
    codex_agent_windows_set_signature(function, [ctypes.c_void_p], ctypes.c_int)
    if function(handle):
        return None
    return codex_agent_windows_os_error("CloseHandle")


def codex_agent_record_close_error(close_errors: list[OSError], close_error: OSError | None) -> None:
    if close_error is not None:
        close_errors.append(close_error)


def codex_agent_note_close_error(primary_error: OSError, close_error: OSError | None) -> OSError:
    if close_error is not None:
        primary_error.add_note(f"CloseHandle failed during cleanup: {close_error}")
    return primary_error


def codex_agent_windows_file_info(handle: int) -> _WindowsByHandleFileInformation:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.GetFileInformationByHandle
    codex_agent_windows_set_signature(
        function,
        [ctypes.c_void_p, ctypes.POINTER(_WindowsByHandleFileInformation)],
        ctypes.c_int,
    )
    info = _WindowsByHandleFileInformation()
    if not function(handle, ctypes.byref(info)):
        raise codex_agent_windows_os_error("GetFileInformationByHandle")
    return info


def codex_agent_windows_inode(info: _WindowsByHandleFileInformation) -> int:
    return (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow)


def codex_agent_windows_identity(info: _WindowsByHandleFileInformation) -> tuple[int, int]:
    return int(info.dwVolumeSerialNumber), codex_agent_windows_inode(info)


def codex_agent_windows_seek_start(handle: int) -> None:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.SetFilePointerEx
    codex_agent_windows_set_signature(
        function,
        [ctypes.c_void_p, ctypes.c_longlong, ctypes.c_void_p, ctypes.c_uint32],
        ctypes.c_int,
    )
    if not function(handle, ctypes.c_longlong(0), None, WINDOWS_FILE_BEGIN):
        raise codex_agent_windows_os_error("SetFilePointerEx")


def codex_agent_windows_read_all(handle: int) -> bytes:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.ReadFile
    codex_agent_windows_set_signature(
        function,
        [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p],
        ctypes.c_int,
    )
    chunks: list[bytes] = []
    while True:
        buffer = ctypes.create_string_buffer(65536)
        bytes_read = ctypes.c_uint32(0)
        if not function(handle, buffer, len(buffer), ctypes.byref(bytes_read), None):
            raise codex_agent_windows_os_error("ReadFile")
        if bytes_read.value == 0:
            break
        chunks.append(buffer.raw[: bytes_read.value])
    return b"".join(chunks)


def codex_agent_windows_write_all(handle: int, content: bytes) -> None:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.WriteFile
    codex_agent_windows_set_signature(
        function,
        [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p],
        ctypes.c_int,
    )
    view = memoryview(content)
    written = 0
    while written < len(view):
        chunk = bytes(view[written : written + 65536])
        buffer = ctypes.create_string_buffer(chunk)
        bytes_written = ctypes.c_uint32(0)
        if not function(handle, buffer, len(chunk), ctypes.byref(bytes_written), None):
            raise codex_agent_windows_os_error("WriteFile")
        if bytes_written.value <= 0:
            raise OSError("Windows write made no progress")
        written += int(bytes_written.value)


def codex_agent_windows_flush(handle: int) -> None:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.FlushFileBuffers
    codex_agent_windows_set_signature(function, [ctypes.c_void_p], ctypes.c_int)
    if not function(handle):
        raise codex_agent_windows_os_error("FlushFileBuffers")


def codex_agent_windows_attributes_for_mode(mode: int) -> int:
    return WINDOWS_FILE_ATTRIBUTE_READONLY if stat.S_IMODE(mode) & 0o222 == 0 else WINDOWS_FILE_ATTRIBUTE_NORMAL


def codex_agent_windows_set_mode_by_handle(handle: int, mode: int) -> None:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.SetFileInformationByHandle
    codex_agent_windows_set_signature(
        function,
        [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32],
        ctypes.c_int,
    )
    basic_info = _WindowsFileBasicInfo()
    basic_info.FileAttributes = codex_agent_windows_attributes_for_mode(mode)
    if not function(handle, WINDOWS_FILE_BASIC_INFO_CLASS, ctypes.byref(basic_info), ctypes.sizeof(basic_info)):
        raise codex_agent_windows_os_error("SetFileInformationByHandle")


def codex_agent_windows_delete_by_handle(handle: int) -> None:
    kernel32 = codex_agent_windows_kernel32()
    function = kernel32.SetFileInformationByHandle
    codex_agent_windows_set_signature(
        function,
        [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32],
        ctypes.c_int,
    )
    disposition = _WindowsFileDispositionInfo()
    disposition.DeleteFile = 1
    if not function(
        handle,
        WINDOWS_FILE_DISPOSITION_INFO_CLASS,
        ctypes.byref(disposition),
        ctypes.sizeof(disposition),
    ):
        raise codex_agent_windows_os_error("SetFileInformationByHandle")


def codex_agent_windows_file_rename_info(target_name: str, directory_handle: int) -> tuple[ctypes.Array[Any], int]:
    encoded_name = target_name.encode("utf-16le")
    offset = WINDOWS_FILE_RENAME_INFO_FILENAME_OFFSET
    buffer = ctypes.create_string_buffer(offset + len(encoded_name))
    header = _WindowsFileRenameInfoHeader.from_buffer(buffer)
    header.ReplaceIfExists = 0
    header.RootDirectory = directory_handle
    header.FileNameLength = len(encoded_name)
    ctypes.memmove(ctypes.addressof(buffer) + offset, encoded_name, len(encoded_name))
    return buffer, len(buffer)


def codex_agent_windows_rename_no_replace(
    agent_dir: "AnchoredAgentDir",
    source_name: str,
    target_name: str,
) -> None:
    agent_dir._validate_name(source_name)
    agent_dir._validate_name(target_name)
    source_handle: int | None = None
    primary_error: OSError | None = None
    close_error: OSError | None = None
    rename_outcome = "unknown"
    try:
        source_handle = codex_agent_windows_create_file(
            agent_dir.path(source_name),
            WINDOWS_DELETE | WINDOWS_SYNCHRONIZE,
            WINDOWS_FILE_SHARE_READ | WINDOWS_FILE_SHARE_WRITE,
            WINDOWS_OPEN_EXISTING,
            WINDOWS_FILE_ATTRIBUTE_NORMAL | WINDOWS_FILE_FLAG_OPEN_REPARSE_POINT,
        )
        rename_info, rename_info_size = codex_agent_windows_file_rename_info(target_name, agent_dir.directory_fd)
        kernel32 = codex_agent_windows_kernel32()
        function = kernel32.SetFileInformationByHandle
        codex_agent_windows_set_signature(
            function,
            [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32],
            ctypes.c_int,
        )
        if not function(source_handle, WINDOWS_FILE_RENAME_INFO_CLASS, rename_info, rename_info_size):
            rename_outcome = "not_committed"
            raise codex_agent_windows_os_error("SetFileInformationByHandle", agent_dir.path(target_name))
        rename_outcome = "committed"
    except OSError as exc:
        primary_error = exc
    finally:
        if source_handle is not None:
            close_error = codex_agent_windows_close_handle(source_handle)
    if primary_error is not None:
        if close_error is not None:
            raise CodexAgentWindowsRenameFailure(
                source_name,
                target_name,
                primary_error,
                close_error,
                rename_outcome,
            ) from primary_error
        raise codex_agent_note_close_error(primary_error, close_error)
    if close_error is not None:
        raise CodexAgentWindowsRenameCommittedCloseFailure(source_name, target_name, close_error)


class AnchoredAgentDir:
    """Descriptor-backed view of the Codex agent destination directory."""

    def __init__(self, destination: Path, identity: tuple[int, int], directory_fd: int) -> None:
        self.destination = destination
        self.identity = identity
        self.directory_fd = directory_fd
        self.closed = False
        self.cleanup_errors: list[dict[str, str]] = []

    @classmethod
    def open(cls, destination: Path, identity: tuple[int, int] | None = None) -> "AnchoredAgentDir":
        if os.name == "nt":
            return WindowsAnchoredAgentDir.open(destination, identity)
        if not (CODEX_AGENT_OPEN_SUPPORTS_DIR_FD and CODEX_AGENT_UNLINK_SUPPORTS_DIR_FD):
            raise OSError(errno.ENOTSUP, "descriptor-relative anchored directory operations are unavailable")
        if identity is None:
            identity = codex_agent_destination_identity(destination)
        descriptor = codex_agent_open_anchored_directory(destination, identity)
        return cls(destination, identity, descriptor)

    def matches(self, destination: Path, identity: tuple[int, int] | None) -> bool:
        return (
            not self.closed
            and self.destination == destination
            and (identity is None or self.identity == identity)
        )

    def close(self, close_errors: list[OSError] | None = None) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            os.close(self.directory_fd)
        except OSError as exc:
            if close_errors is not None:
                close_errors.append(exc)

    def record_cleanup_result(self, result: CodexAgentCleanupResult) -> None:
        self.cleanup_errors.extend(result.cleanup_errors)

    def is_current(self) -> bool:
        try:
            return codex_agent_destination_identity(self.destination) == self.identity
        except OSError:
            return False

    def evidence_path(self, name: str) -> str:
        self._validate_name(name)
        if self.is_current():
            return (self.destination / name).as_posix()
        return f"anchored-agent-dir:{self.identity[0]}:{self.identity[1]}/{name}"

    def evidence_subpath(self, *names: str) -> str:
        for name in names:
            self._validate_name(name)
        if self.is_current():
            return self.destination.joinpath(*names).as_posix()
        return f"anchored-agent-dir:{self.identity[0]}:{self.identity[1]}/{'/'.join(names)}"

    def path(self, name: str) -> Path:
        self._validate_name(name)
        return self.destination / name

    def ensure_current(self, message: str) -> None:
        if not self.is_current():
            raise OSError(message)

    def target_is_safe(self, name: str) -> bool:
        self._validate_name(name)
        try:
            metadata = os.stat(name, dir_fd=self.directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return stat.S_ISREG(metadata.st_mode)

    def previous_state(self, name: str) -> CodexAgentFileState | None:
        self._validate_name(name)
        return codex_agent_previous_state_at(self.directory_fd, name)

    def state_matches(self, name: str, expected: CodexAgentFileState | None) -> bool:
        try:
            return self.previous_state(name) == expected
        except OSError:
            return False

    def create_temp_file(self, target_name: str, content: bytes, mode: int | None) -> str:
        self._validate_name(target_name)
        for _ in range(32):
            temp_name = f".{target_name}.{secrets.token_hex(12)}.tmp"
            descriptor: int | None = None
            created = False
            try:
                descriptor = os.open(
                    temp_name,
                    os.O_RDWR
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_BINARY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=self.directory_fd,
                )
                created = True
                view = memoryview(content)
                written = 0
                while written < len(view):
                    count = os.write(descriptor, view[written:])
                    if count <= 0:
                        raise OSError("temporary install write made no progress")
                    written += count
                if mode is not None:
                    descriptor_chmod = getattr(os, "fchmod", None)
                    if not callable(descriptor_chmod):
                        raise OSError("safe descriptor-based mode restoration is unavailable")
                    descriptor_chmod(descriptor, mode & 0o7777)
                os.fsync(descriptor)
                return temp_name
            except FileExistsError:
                continue
            except OSError as exc:
                if created:
                    cleanup_result = self.preserve_uncertain_entry(temp_name, "temp_state_capture_unavailable")
                    if cleanup_result:
                        raise CodexAgentNoClobberConflict(
                            str(exc),
                            cleanup_result.preserved_paths,
                            cleanup_result.cleanup_errors,
                        ) from exc
                raise
            finally:
                if descriptor is not None:
                    codex_agent_close_descriptor_nonmasking(descriptor)
        raise OSError("could not allocate a collision-free temporary install file")

    def link_no_replace(self, source_name: str, target_name: str) -> None:
        self._validate_name(source_name)
        self._validate_name(target_name)
        os.link(
            source_name,
            target_name,
            src_dir_fd=self.directory_fd,
            dst_dir_fd=self.directory_fd,
            follow_symlinks=False,
        )

    def rename_no_replace(self, source_name: str, target_name: str) -> None:
        self._validate_name(source_name)
        self._validate_name(target_name)
        codex_agent_native_rename_no_replace(self.directory_fd, source_name, target_name)

    def preserved_cleanup_entry(self, path: str, error: str) -> dict[str, str]:
        return {
            "kind": "preserved_cleanup_entry",
            "target": path,
            "error": error,
        }

    def preserved_concurrent_file(self, path: str, error: str) -> dict[str, str]:
        return {
            "kind": "preserved_concurrent_file",
            "target": path,
            "error": error,
        }

    def classify_entry_by_expected(
        self,
        name: str,
        expected_state: CodexAgentFileState,
        error: str,
        *,
        exact_is_cleanup: bool = True,
    ) -> CodexAgentCleanupResult:
        self._validate_name(name)
        evidence_path = self.evidence_path(name)
        try:
            current_state = self.previous_state(name)
        except OSError:
            return CodexAgentCleanupResult(
                public_conflicts=[evidence_path],
                cleanup_errors=[self.preserved_concurrent_file(evidence_path, error)],
            )
        if current_state is None:
            return CodexAgentCleanupResult()
        if current_state == expected_state:
            cleanup_errors = [self.preserved_cleanup_entry(evidence_path, error)] if exact_is_cleanup else []
            return CodexAgentCleanupResult(
                public_conflicts=[evidence_path],
                cleanup_errors=cleanup_errors,
            )
        return CodexAgentCleanupResult(
            public_conflicts=[evidence_path],
            cleanup_errors=[self.preserved_concurrent_file(evidence_path, error)],
        )

    def close_handle_cleanup_error(self, name: str, close_error: OSError) -> dict[str, str]:
        self._validate_name(name)
        return {
            "kind": "close_handle",
            "target": self.evidence_path(name),
            "error": type(close_error).__name__,
        }

    def close_handle_cleanup_errors_for_rename(
        self,
        exc: CodexAgentWindowsRenameFailure,
    ) -> list[dict[str, str]]:
        if exc.close_error is None:
            return []
        if exc.outcome == "committed":
            names = [exc.target_name]
        elif exc.outcome == "not_committed":
            names = [exc.source_name]
        else:
            names = [exc.source_name, exc.target_name]
        return [self.close_handle_cleanup_error(name, exc.close_error) for name in dict.fromkeys(names)]

    def merge_cleanup_result(self, result: CodexAgentCleanupResult, extra: CodexAgentCleanupResult) -> None:
        result.public_conflicts = list(dict.fromkeys([*result.public_conflicts, *extra.public_conflicts]))
        result.preserved_private_paths = list(
            dict.fromkeys([*result.preserved_private_paths, *extra.preserved_private_paths])
        )
        result.cleanup_errors.extend(extra.cleanup_errors)

    def preserve_path_unknown(
        self,
        preserved_paths: list[str],
        cleanup_errors: list[dict[str, str]],
        path: str,
        error: str,
    ) -> None:
        if path not in preserved_paths:
            preserved_paths.append(path)
        record = self.preserved_concurrent_file(path, error)
        if record not in cleanup_errors:
            cleanup_errors.append(record)

    def previous_state_exists_for_packaging(
        self,
        name: str,
        preserved_paths: list[str],
        cleanup_errors: list[dict[str, str]],
        error: str,
    ) -> bool:
        try:
            return self.previous_state(name) is not None
        except OSError:
            self.preserve_path_unknown(preserved_paths, cleanup_errors, self.evidence_path(name), error)
            return True

    def cleanup_entry_for_packaging(
        self,
        name: str,
        expected_state: CodexAgentFileState,
        preserved_paths: list[str],
        cleanup_errors: list[dict[str, str]],
        error: str,
    ) -> None:
        try:
            cleanup = self.cleanup_owned_entry(name, expected_state)
        except OSError:
            self.preserve_path_unknown(preserved_paths, cleanup_errors, self.evidence_path(name), error)
            return
        cleanup_errors.extend(cleanup.cleanup_errors)
        if cleanup.preserved_paths:
            preserved_paths.extend(cleanup.preserved_paths)
        else:
            path = self.evidence_path(name)
            preserved_paths[:] = [preserved for preserved in preserved_paths if preserved != path]

    def restore_failure_for_packaging(
        self,
        exc: OSError,
        backup_name: str,
        target_name: str,
        preserved_paths: list[str],
        cleanup_errors: list[dict[str, str]],
        error: str,
    ) -> None:
        if isinstance(exc, CodexAgentNoClobberConflict):
            preserved_paths.extend(exc.preserved_paths)
            cleanup_errors.extend(exc.cleanup_errors)
        elif isinstance(exc, CodexAgentRecoveryCopyFailure):
            cleanup_errors.extend(
                {"kind": "recovery_copy_failed", "target": path, "error": "recovery_copy_incomplete"}
                for path in exc.failed_paths
            )
            for path in exc.preserved_paths:
                self.preserve_path_unknown(preserved_paths, cleanup_errors, path, error)
        self.preserve_path_unknown(preserved_paths, cleanup_errors, self.evidence_path(backup_name), error)
        self.preserve_path_unknown(preserved_paths, cleanup_errors, self.evidence_path(target_name), error)

    def cleanup_owned_entry(
        self,
        name: str,
        expected_state: CodexAgentFileState,
    ) -> CodexAgentCleanupResult:
        self._validate_name(name)
        try:
            current_state = self.previous_state(name)
        except OSError:
            return CodexAgentCleanupResult(public_conflicts=[self.evidence_path(name)])
        if current_state is None:
            return CodexAgentCleanupResult()
        if current_state != expected_state:
            return CodexAgentCleanupResult(public_conflicts=[self.evidence_path(name)])

        cleanup_name: str | None = None
        for _ in range(32):
            candidate = f".{secrets.token_hex(12)}.cleanup.{name}"
            try:
                self.rename_no_replace(name, candidate)
                cleanup_name = candidate
                break
            except FileExistsError:
                continue
            except FileNotFoundError:
                return CodexAgentCleanupResult()
        if cleanup_name is None:
            return CodexAgentCleanupResult(public_conflicts=[self.evidence_path(name)])

        try:
            moved_state = self.previous_state(cleanup_name)
        except OSError:
            moved_state = None
        if moved_state != expected_state:
            try:
                self.rename_no_replace(cleanup_name, name)
            except OSError:
                result = self.classify_entry_by_expected(cleanup_name, expected_state, "cleanup_restore_collision")
                self.merge_cleanup_result(
                    result,
                    self.classify_entry_by_expected(name, expected_state, "cleanup_restore_collision"),
                )
                return result
            result = CodexAgentCleanupResult()
            self.merge_cleanup_result(
                result,
                self.classify_entry_by_expected(cleanup_name, expected_state, "cleanup_restore_collision"),
            )
            self.merge_cleanup_result(
                result,
                self.classify_entry_by_expected(name, expected_state, "cleanup_restore_collision"),
            )
            return result

        return self.cleanup_verified_quarantine(cleanup_name, expected_state)

    def preserve_uncertain_entry(self, name: str, error: str) -> CodexAgentCleanupResult:
        self._validate_name(name)
        evidence_path = self.evidence_path(name)
        try:
            state = self.previous_state(name)
        except OSError:
            return CodexAgentCleanupResult(
                public_conflicts=[evidence_path],
                cleanup_errors=[{"kind": "preserved_concurrent_file", "target": evidence_path, "error": error}],
            )
        if state is None:
            return CodexAgentCleanupResult()
        return CodexAgentCleanupResult(
            public_conflicts=[evidence_path],
            cleanup_errors=[{"kind": "preserved_concurrent_file", "target": evidence_path, "error": error}],
        )

    def cleanup_verified_quarantine(
        self,
        cleanup_name: str,
        expected_state: CodexAgentFileState,
    ) -> CodexAgentCleanupResult:
        self._validate_name(cleanup_name)
        private_dir_name: str | None = None
        private_dir_fd: int | None = None
        private_entry_name = cleanup_name
        final_result: CodexAgentCleanupResult | None = None

        def public_entry_classification(error: str) -> tuple[list[str], list[dict[str, str]]]:
            public_path = self.evidence_path(cleanup_name)
            try:
                public_state = self.previous_state(cleanup_name)
            except OSError:
                return [public_path], [self.preserved_concurrent_file(public_path, error)]
            if public_state is None:
                return [], []
            if public_state == expected_state:
                return [public_path], [self.preserved_cleanup_entry(public_path, error)]
            return [public_path], [self.preserved_concurrent_file(public_path, error)]

        def private_entry_classification(error: str) -> tuple[list[str], list[dict[str, str]]]:
            if private_dir_fd is None or private_dir_name is None:
                return [], []
            private_path = self.evidence_subpath(private_dir_name, private_entry_name)
            try:
                private_state = codex_agent_previous_state_at(private_dir_fd, private_entry_name)
            except OSError:
                return [private_path], [self.preserved_concurrent_file(private_path, error)]
            if private_state is None:
                return [], []
            if private_state == expected_state:
                return [private_path], [self.preserved_cleanup_entry(private_path, error)]
            return [private_path], [self.preserved_concurrent_file(private_path, error)]

        def classified_quarantine_result(error: str) -> CodexAgentCleanupResult:
            public_paths, public_errors = public_entry_classification(error)
            private_paths, private_errors = private_entry_classification(error)
            return CodexAgentCleanupResult(
                public_conflicts=list(dict.fromkeys(public_paths)),
                preserved_private_paths=list(dict.fromkeys(private_paths)),
                cleanup_errors=[*public_errors, *private_errors],
            )

        def remember(result: CodexAgentCleanupResult) -> CodexAgentCleanupResult:
            nonlocal final_result
            final_result = result
            return result

        def private_dir_path() -> str:
            return self.evidence_path(private_dir_name or "")

        def append_private_dir_unknown(result: CodexAgentCleanupResult, error: str) -> None:
            if private_dir_name is None:
                return
            path = private_dir_path()
            if path not in result.preserved_private_paths:
                result.preserved_private_paths.append(path)
            record = self.preserved_concurrent_file(path, error)
            if record not in result.cleanup_errors:
                result.cleanup_errors.append(record)

        def preserve_private_dir_unknown(result: CodexAgentCleanupResult, error: str) -> None:
            if private_dir_name is None:
                return
            append_private_dir_unknown(result, error)

        try:
            for _ in range(32):
                candidate = f".{secrets.token_hex(12)}.cleanup-dir"
                try:
                    os.mkdir(candidate, 0o700, dir_fd=self.directory_fd)
                    private_dir_name = candidate
                    break
                except FileExistsError:
                    continue
                except OSError:
                    return remember(classified_quarantine_result("private_quarantine_dir_unavailable"))
            if private_dir_name is None:
                return remember(classified_quarantine_result("private_quarantine_dir_unavailable"))
            try:
                private_dir_fd = os.open(
                    private_dir_name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=self.directory_fd,
                )
            except OSError:
                result = classified_quarantine_result("private_quarantine_open_failed")
                preserve_private_dir_unknown(result, "private_quarantine_open_failed")
                return remember(result)
            try:
                codex_agent_native_rename_no_replace_between(
                    self.directory_fd,
                    cleanup_name,
                    private_dir_fd,
                    private_entry_name,
                )
            except FileNotFoundError:
                return remember(classified_quarantine_result("private_quarantine_file_not_found"))
            except FileExistsError:
                return remember(classified_quarantine_result("private_quarantine_collision"))
            except OSError:
                return remember(classified_quarantine_result("private_quarantine_move_failed"))
            # POSIX has no delete-by-descriptor. Hold the verified inode open, unlink its
            # name inside the private directory, then require the held inode to have lost
            # its last link. A swapped name leaves the held inode linked: fail closed.
            try:
                held_fd = os.open(
                    private_entry_name,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
                    dir_fd=private_dir_fd,
                )
            except OSError:
                return remember(classified_quarantine_result("private_quarantine_identity_mismatch"))
            try:
                try:
                    held_metadata = os.fstat(held_fd)
                    private_state = codex_agent_previous_state_at(private_dir_fd, private_entry_name)
                except OSError:
                    return remember(classified_quarantine_result("private_quarantine_identity_mismatch"))
                if (
                    private_state != expected_state
                    or (held_metadata.st_dev, held_metadata.st_ino) != (expected_state.device, expected_state.inode)
                ):
                    return remember(classified_quarantine_result("private_quarantine_identity_mismatch"))
                if held_metadata.st_nlink != 1:
                    return remember(classified_quarantine_result("private_quarantine_multiple_links"))
                if not self.is_current():
                    return remember(classified_quarantine_result("private_quarantine_destination_changed"))
                try:
                    os.unlink(private_entry_name, dir_fd=private_dir_fd)
                except OSError:
                    return remember(classified_quarantine_result("private_quarantine_unlink_failed"))
                try:
                    unlinked = os.fstat(held_fd).st_nlink == 0
                except OSError:
                    unlinked = False
                if not unlinked:
                    result = classified_quarantine_result("private_quarantine_unlink_identity_mismatch")
                    append_private_dir_unknown(result, "private_quarantine_unlink_identity_mismatch")
                    return remember(result)
                return remember(CodexAgentCleanupResult())
            finally:
                try:
                    os.close(held_fd)
                except OSError:
                    # The unlink result is already decided; a failed close cannot change it.
                    pass
        finally:
            if private_dir_fd is not None:
                try:
                    os.close(private_dir_fd)
                except OSError as exc:
                    if final_result is not None:
                        final_result.cleanup_errors.append(
                            {"kind": "close_descriptor", "target": private_dir_path(), "error": type(exc).__name__}
                        )
            if private_dir_name is not None and (
                final_result is None or private_dir_path() not in final_result.preserved_private_paths
            ):
                try:
                    os.rmdir(private_dir_name, dir_fd=self.directory_fd)
                except OSError as exc:
                    if final_result is not None and exc.errno in {errno.ENOTEMPTY, errno.EEXIST}:
                        append_private_dir_unknown(final_result, "private_quarantine_dir_not_empty")
                    elif final_result is not None:
                        final_result.cleanup_errors.append(
                            {"kind": "remove_directory", "target": private_dir_path(), "error": type(exc).__name__}
                        )
                        if not final_result.preserved_private_paths:
                            final_result.preserved_private_paths.append(private_dir_path())

    def move_target_to_backup(
        self,
        target_name: str,
        expected_state: CodexAgentFileState | None = None,
    ) -> str:
        self._validate_name(target_name)
        del expected_state
        moved_name: str | None = None
        for _ in range(32):
            candidate = f".{target_name}.{secrets.token_hex(12)}.bak"
            try:
                self.rename_no_replace(target_name, candidate)
                moved_name = candidate
                break
            except FileExistsError:
                continue
        if moved_name is None:
            raise OSError("could not allocate a collision-free backup name")
        return moved_name

    def restore_backup_no_clobber(self, backup_name: str, target_name: str) -> None:
        self._validate_name(backup_name)
        self._validate_name(target_name)
        backup_state = self.previous_state(backup_name)
        if backup_state is None:
            raise OSError(f"preserved backup disappeared before restore: {backup_name}")
        try:
            self.rename_no_replace(backup_name, target_name)
        except OSError as exc:
            result = CodexAgentCleanupResult()
            error = "backup_restore_rename_failed"
            if isinstance(exc, CodexAgentWindowsRenameFailure) and exc.close_error is not None:
                result.cleanup_errors.extend(self.close_handle_cleanup_errors_for_rename(exc))
            if isinstance(exc, CodexAgentWindowsRenameCommittedCloseFailure):
                error = "backup_restore_rename_close_failure"
            self.merge_cleanup_result(
                result,
                self.classify_entry_by_expected(backup_name, backup_state, error),
            )
            self.merge_cleanup_result(
                result,
                self.classify_entry_by_expected(target_name, backup_state, error, exact_is_cleanup=False),
            )
            raise CodexAgentNoClobberConflict(
                f"could not restore moved target without clobbering concurrent state: {backup_name}",
                result.preserved_paths,
                result.cleanup_errors,
            ) from exc
        restored_state = self.previous_state(target_name)
        if restored_state != backup_state:
            preserved = self.preserve_state_as_backup(backup_state, target_name)
            raise CodexAgentNoClobberConflict(
                f"restored target changed during backup cleanup: {backup_name}",
                [preserved, self.evidence_path(target_name)],
            )
        if not self.is_current():
            raise CodexAgentRecoveryCopyFailure(
                "destination moved before anchored restore evidence",
                [],
                [self.evidence_path(target_name)],
            )

    def preserve_state_as_backup(self, state: CodexAgentFileState, target_name: str) -> str:
        self._validate_name(target_name)
        preserved_fd: int | None = None
        preserved_name: str | None = None
        created = False
        primary_error: OSError | None = None
        close_errors: list[OSError] = []
        try:
            for _ in range(32):
                preserved_name = f".{target_name}.{secrets.token_hex(12)}.bak"
                try:
                    preserved_fd = os.open(
                        preserved_name,
                        os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                        state.mode & 0o7777,
                        dir_fd=self.directory_fd,
                    )
                    created = True
                    break
                except FileExistsError:
                    preserved_name = None
            if preserved_fd is None or preserved_name is None:
                raise OSError("could not allocate exclusive anchored recovery copy")
            view = memoryview(state.content)
            written = 0
            while written < len(view):
                count = os.write(preserved_fd, view[written:])
                if count <= 0:
                    raise OSError("recovery copy write made no progress")
                written += count
            descriptor_chmod = getattr(os, "fchmod", None)
            if not callable(descriptor_chmod):
                raise OSError("safe descriptor-based mode preservation is unavailable")
            descriptor_chmod(preserved_fd, state.mode & 0o7777)
            os.fsync(preserved_fd)
            os.lseek(preserved_fd, 0, os.SEEK_SET)
            restored = bytearray()
            while True:
                chunk = os.read(preserved_fd, 65536)
                if not chunk:
                    break
                restored.extend(chunk)
            preserved_metadata = os.fstat(preserved_fd)
            if bytes(restored) != state.content or stat.S_IMODE(preserved_metadata.st_mode) != stat.S_IMODE(state.mode):
                raise OSError("preserved prior-state backup verification failed")
            if not self.is_current():
                raise OSError("destination moved before recovery-copy evidence")
        except OSError as exc:
            primary_error = exc
        finally:
            if preserved_fd is not None:
                try:
                    os.close(preserved_fd)
                except OSError as exc:
                    close_errors.append(exc)
        if primary_error is not None or close_errors:
            failed_paths: list[str] = []
            if created and preserved_name is not None:
                failed_paths.append(self.evidence_path(preserved_name))
            preserved_paths: list[str] = []
            try:
                target_state = self.previous_state(target_name)
            except OSError:
                preserved_paths.append(self.evidence_path(target_name))
            else:
                if target_state is not None:
                    preserved_paths.append(self.evidence_path(target_name))
            detail = ""
            if close_errors:
                detail = f"; descriptor cleanup errors={len(close_errors)}"
            error = CodexAgentRecoveryCopyFailure(
                f"could not create a verified anchored recovery copy{detail}",
                failed_paths,
                preserved_paths,
            )
            if primary_error is not None:
                raise error from primary_error
            raise error from close_errors[0]
        if preserved_name is None:
            raise CodexAgentRecoveryCopyFailure("anchored recovery copy produced no result", [], [])
        return self.evidence_path(preserved_name)

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or name in {".", ".."} or "/" in name or "\\" in name:
            raise OSError("unsafe anchored agent entry name")


class WindowsAnchoredAgentDir(AnchoredAgentDir):
    """Windows directory-handle backend held without FILE_SHARE_DELETE."""

    @classmethod
    def open(cls, destination: Path, identity: tuple[int, int] | None = None) -> "WindowsAnchoredAgentDir":
        handle = codex_agent_windows_create_file(
            destination,
            WINDOWS_FILE_READ_ATTRIBUTES,
            WINDOWS_FILE_SHARE_READ | WINDOWS_FILE_SHARE_WRITE,
            WINDOWS_OPEN_EXISTING,
            WINDOWS_FILE_FLAG_BACKUP_SEMANTICS | WINDOWS_FILE_FLAG_OPEN_REPARSE_POINT,
        )
        try:
            info = codex_agent_windows_file_info(handle)
            if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT:
                raise OSError("destination is not a stable directory")
            if not info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_DIRECTORY:
                raise OSError("destination is not a stable directory")
            handle_identity = codex_agent_windows_identity(info)
            if identity is not None and handle_identity != identity:
                raise OSError("destination changed before anchored operation")
        except OSError as exc:
            close_error = codex_agent_windows_close_handle(handle)
            codex_agent_note_close_error(exc, close_error)
            raise
        return cls(destination, handle_identity, handle)

    def close(self, close_errors: list[OSError] | None = None) -> None:
        if self.closed:
            return
        self.closed = True
        close_error = codex_agent_windows_close_handle(self.directory_fd)
        if close_error is not None:
            if close_errors is not None:
                close_errors.append(close_error)
            else:
                raise close_error

    def target_is_safe(self, name: str) -> bool:
        self._validate_name(name)
        handle: int | None = None
        result = False
        primary_error: OSError | None = None
        try:
            handle = self.open_child_handle(
                name,
                WINDOWS_FILE_READ_ATTRIBUTES,
                WINDOWS_FILE_SHARE_READ | WINDOWS_FILE_SHARE_WRITE,
                WINDOWS_OPEN_EXISTING,
            )
            info = codex_agent_windows_file_info(handle)
            if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT:
                result = False
            else:
                result = not bool(info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_DIRECTORY)
        except FileNotFoundError:
            result = True
        except OSError as exc:
            primary_error = exc
            result = False
        finally:
            if handle is not None:
                close_error = codex_agent_windows_close_handle(handle)
                if close_error is not None:
                    if primary_error is not None:
                        raise codex_agent_note_close_error(primary_error, close_error)
                    raise close_error
        return result

    def previous_state(self, name: str) -> CodexAgentFileState | None:
        self._validate_name(name)
        handle: int | None = None
        result: CodexAgentFileState | None = None
        primary_error: OSError | None = None
        try:
            handle = self.open_child_handle(
                name,
                WINDOWS_GENERIC_READ,
                WINDOWS_FILE_SHARE_READ,
                WINDOWS_OPEN_EXISTING,
            )
            info = codex_agent_windows_file_info(handle)
            if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT:
                raise OSError("managed target is not a regular file")
            if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_DIRECTORY:
                raise OSError("managed target is not a regular file")
            content = codex_agent_windows_read_all(handle)
            try:
                mode = self.path(name).stat().st_mode
            except OSError:
                mode = stat.S_IFREG | 0o600
            result = CodexAgentFileState(
                content=content,
                mode=mode,
                device=int(info.dwVolumeSerialNumber),
                inode=codex_agent_windows_inode(info),
            )
        except FileNotFoundError:
            result = None
        except OSError as exc:
            primary_error = exc
        finally:
            close_error: OSError | None = None
            if handle is not None:
                close_error = codex_agent_windows_close_handle(handle)
            if primary_error is not None:
                raise codex_agent_note_close_error(primary_error, close_error)
            if close_error is not None:
                raise close_error
        return result

    def create_temp_file(self, target_name: str, content: bytes, mode: int | None) -> str:
        self._validate_name(target_name)
        for _ in range(32):
            temp_name = f".{target_name}.{secrets.token_hex(12)}.tmp"
            handle: int | None = None
            created = False
            try:
                handle = self.open_child_handle(
                    temp_name,
                    WINDOWS_GENERIC_READ | WINDOWS_GENERIC_WRITE,
                    0,
                    WINDOWS_CREATE_NEW,
                )
                created = True
                codex_agent_windows_write_all(handle, content)
                codex_agent_windows_flush(handle)
                if mode is not None:
                    codex_agent_windows_set_mode_by_handle(handle, mode)
                close_error = codex_agent_windows_close_handle(handle)
                handle = None
                if close_error is not None:
                    cleanup_error = {
                        "kind": "close_handle",
                        "target": self.evidence_path(temp_name),
                        "error": type(close_error).__name__,
                    }
                    cleanup_result = self.preserve_uncertain_entry(temp_name, "close_handle")
                    raise CodexAgentNoClobberConflict(
                        "temporary install file close failed",
                        cleanup_result.preserved_paths,
                        [cleanup_error, *cleanup_result.cleanup_errors],
                    ) from close_error
                return temp_name
            except FileExistsError:
                continue
            except CodexAgentNoClobberConflict:
                raise
            except OSError as exc:
                cleanup_errors: list[dict[str, str]] = []
                cleanup_result = CodexAgentCleanupResult()
                expected_temp_state: CodexAgentFileState | None = None
                if created and handle is not None:
                    try:
                        codex_agent_windows_seek_start(handle)
                        temp_content = codex_agent_windows_read_all(handle)
                        temp_info = codex_agent_windows_file_info(handle)
                        expected_temp_state = CodexAgentFileState(
                            content=temp_content,
                            mode=stat.S_IFREG | 0o600,
                            device=int(temp_info.dwVolumeSerialNumber),
                            inode=codex_agent_windows_inode(temp_info),
                        )
                    except OSError:
                        expected_temp_state = None
                if handle is not None:
                    close_error = codex_agent_windows_close_handle(handle)
                    if close_error is not None:
                        cleanup_errors.append(
                            {
                                "kind": "close_handle",
                                "target": self.evidence_path(temp_name),
                                "error": type(close_error).__name__,
                            }
                        )
                    handle = None
                if created:
                    if expected_temp_state is not None:
                        cleanup_result = self.cleanup_owned_entry(temp_name, expected_temp_state)
                    else:
                        cleanup_result = self.preserve_uncertain_entry(temp_name, "temp_state_capture_unavailable")
                cleanup_errors = [*cleanup_errors, *cleanup_result.cleanup_errors]
                if cleanup_errors or cleanup_result.preserved_paths:
                    raise CodexAgentNoClobberConflict(str(exc), cleanup_result.preserved_paths, cleanup_errors) from exc
                raise
            finally:
                if handle is not None:
                    close_error = codex_agent_windows_close_handle(handle)
                    if close_error is not None:
                        self.record_cleanup_result(
                            CodexAgentCleanupResult(
                                cleanup_errors=[
                                    {
                                        "kind": "close_handle",
                                        "target": self.evidence_path(temp_name),
                                        "error": type(close_error).__name__,
                                    }
                                ]
                            )
                        )
        raise OSError("could not allocate a collision-free temporary install file")

    def link_no_replace(self, source_name: str, target_name: str) -> None:
        self._validate_name(source_name)
        self._validate_name(target_name)
        kernel32 = codex_agent_windows_kernel32()
        function = kernel32.CreateHardLinkW
        codex_agent_windows_set_signature(
            function,
            [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p],
            ctypes.c_int,
        )
        if not function(str(self.path(target_name)), str(self.path(source_name)), None):
            raise codex_agent_windows_os_error("CreateHardLinkW", self.path(target_name))

    def rename_no_replace(self, source_name: str, target_name: str) -> None:
        codex_agent_windows_rename_no_replace(self, source_name, target_name)

    def set_child_mode(self, name: str, mode: int) -> None:
        self._validate_name(name)
        handle: int | None = None
        close_errors: list[OSError] = []
        primary_error: OSError | None = None
        try:
            handle = self.open_child_handle(
                name,
                WINDOWS_FILE_WRITE_ATTRIBUTES,
                WINDOWS_FILE_SHARE_READ | WINDOWS_FILE_SHARE_WRITE,
                WINDOWS_OPEN_EXISTING,
            )
            codex_agent_windows_set_mode_by_handle(handle, mode)
        except OSError as exc:
            primary_error = exc
        finally:
            if handle is not None:
                codex_agent_record_close_error(close_errors, codex_agent_windows_close_handle(handle))
        if primary_error is not None:
            if close_errors:
                raise codex_agent_note_close_error(primary_error, close_errors[0])
            raise primary_error
        if close_errors:
            raise close_errors[0]

    def state_from_handle(self, handle: int) -> CodexAgentFileState:
        info = codex_agent_windows_file_info(handle)
        if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT:
            raise OSError("managed target is not a regular file")
        if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_DIRECTORY:
            raise OSError("managed target is not a regular file")
        codex_agent_windows_seek_start(handle)
        content = codex_agent_windows_read_all(handle)
        readonly = bool(info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_READONLY)
        mode = stat.S_IFREG | (0o400 if readonly else 0o600)
        return CodexAgentFileState(
            content=content,
            mode=mode,
            device=int(info.dwVolumeSerialNumber),
            inode=codex_agent_windows_inode(info),
        )

    def apply_child_mode_verified(
        self,
        name: str,
        mode: int,
        expected_state: CodexAgentFileState,
    ) -> CodexAgentFileState:
        self._validate_name(name)
        handle: int | None = None
        close_errors: list[OSError] = []
        result: CodexAgentFileState | None = None
        primary_error: OSError | None = None
        try:
            handle = self.open_child_handle(
                name,
                WINDOWS_GENERIC_READ | WINDOWS_FILE_WRITE_ATTRIBUTES,
                0,
                WINDOWS_OPEN_EXISTING,
            )
            current_state = self.state_from_handle(handle)
            if (
                current_state.content != expected_state.content
                or current_state.device != expected_state.device
                or current_state.inode != expected_state.inode
            ):
                raise CodexAgentNoClobberConflict(
                    "target changed before Windows mode application",
                    [self.evidence_path(name)],
                )
            codex_agent_windows_set_mode_by_handle(handle, mode)
            result = self.state_from_handle(handle)
        except OSError as exc:
            primary_error = exc
        finally:
            if handle is not None:
                codex_agent_record_close_error(close_errors, codex_agent_windows_close_handle(handle))
        if primary_error is not None:
            if close_errors:
                raise codex_agent_note_close_error(primary_error, close_errors[0])
            raise primary_error
        if close_errors:
            raise close_errors[0]
        if result is None:
            raise OSError("Windows mode application produced no verified state")
        return result

    def cleanup_owned_entry(
        self,
        name: str,
        expected_state: CodexAgentFileState,
    ) -> CodexAgentCleanupResult:
        self._validate_name(name)
        try:
            current_state = self.previous_state(name)
        except OSError:
            return CodexAgentCleanupResult(public_conflicts=[self.evidence_path(name)])
        if current_state is None:
            return CodexAgentCleanupResult()
        if current_state != expected_state:
            return CodexAgentCleanupResult(public_conflicts=[self.evidence_path(name)])
        cleanup_name: str | None = None
        rename_cleanup_errors: list[dict[str, str]] = []
        rename_cleanup_error: str | None = None
        moved_state_after_rename: CodexAgentFileState | None = None
        for _ in range(32):
            candidate = f".{secrets.token_hex(12)}.cleanup.{name}"
            try:
                self.rename_no_replace(name, candidate)
                cleanup_name = candidate
                break
            except FileExistsError:
                continue
            except FileNotFoundError:
                return CodexAgentCleanupResult()
            except OSError as exc:
                try:
                    moved_state = self.previous_state(candidate)
                except OSError:
                    moved_state = None
                error = "cleanup_rename_failed"
                rename_committed_close_failure = isinstance(exc, CodexAgentWindowsRenameCommittedCloseFailure)
                if isinstance(exc, CodexAgentWindowsRenameFailure) and exc.close_error is not None:
                    rename_cleanup_errors.extend(self.close_handle_cleanup_errors_for_rename(exc))
                if rename_committed_close_failure:
                    error = "cleanup_rename_close_failure"
                if moved_state == expected_state or (rename_committed_close_failure and self.path(candidate).exists()):
                    cleanup_name = candidate
                    moved_state_after_rename = expected_state
                    rename_cleanup_error = error
                    break
                result = CodexAgentCleanupResult(cleanup_errors=rename_cleanup_errors)
                self.merge_cleanup_result(
                    result,
                    self.classify_entry_by_expected(candidate, expected_state, error),
                )
                self.merge_cleanup_result(
                    result,
                    self.classify_entry_by_expected(name, expected_state, error, exact_is_cleanup=False),
                )
                return result
        if cleanup_name is None:
            return CodexAgentCleanupResult(public_conflicts=[self.evidence_path(name)])
        if moved_state_after_rename is not None:
            moved_state = moved_state_after_rename
        else:
            try:
                moved_state = self.previous_state(cleanup_name)
            except OSError:
                moved_state = None
        if moved_state != expected_state:
            result = CodexAgentCleanupResult(cleanup_errors=rename_cleanup_errors)
            self.merge_cleanup_result(
                result,
                self.classify_entry_by_expected(cleanup_name, expected_state, "cleanup_moved_state_mismatch"),
            )
            self.merge_cleanup_result(
                result,
                self.classify_entry_by_expected(name, expected_state, "cleanup_moved_state_mismatch"),
            )
            return result
        handle: int | None = None
        result = CodexAgentCleanupResult(cleanup_errors=rename_cleanup_errors)

        def close_cleanup_handle() -> None:
            nonlocal handle
            if handle is None:
                return
            close_error = codex_agent_windows_close_handle(handle)
            handle = None
            if close_error is not None:
                result.cleanup_errors.append(
                    {
                        "kind": "close_handle",
                        "target": self.evidence_path(cleanup_name),
                        "error": type(close_error).__name__,
                    }
                )

        def return_cleanup_verification_mismatch() -> CodexAgentCleanupResult:
            if rename_cleanup_error is not None:
                self.merge_cleanup_result(
                    result,
                    self.classify_entry_by_expected(cleanup_name, expected_state, rename_cleanup_error),
                )
                self.merge_cleanup_result(
                    result,
                    self.classify_entry_by_expected(
                        name,
                        expected_state,
                        rename_cleanup_error,
                        exact_is_cleanup=False,
                    ),
                )
                return result
            result.public_conflicts.append(self.evidence_path(cleanup_name))
            return result

        for _ in range(2):
            try:
                handle = self.open_child_handle(
                    cleanup_name,
                    WINDOWS_GENERIC_READ | WINDOWS_FILE_WRITE_ATTRIBUTES | WINDOWS_DELETE,
                    0,
                    WINDOWS_OPEN_EXISTING,
                )
                info = codex_agent_windows_file_info(handle)
                if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT:
                    return return_cleanup_verification_mismatch()
                if info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_DIRECTORY:
                    return return_cleanup_verification_mismatch()
                if int(info.dwVolumeSerialNumber) != expected_state.device:
                    return return_cleanup_verification_mismatch()
                if codex_agent_windows_inode(info) != expected_state.inode:
                    return return_cleanup_verification_mismatch()
                codex_agent_windows_seek_start(handle)
                if codex_agent_windows_read_all(handle) != expected_state.content:
                    return return_cleanup_verification_mismatch()
                codex_agent_windows_set_mode_by_handle(handle, stat.S_IFREG | 0o600)
                codex_agent_windows_delete_by_handle(handle)
                close_cleanup_handle()
                if self.path(cleanup_name).exists():
                    if rename_cleanup_error is not None:
                        self.merge_cleanup_result(
                            result,
                            self.classify_entry_by_expected(
                                cleanup_name,
                                expected_state,
                                rename_cleanup_error,
                            ),
                        )
                    else:
                        result.public_conflicts.append(self.evidence_path(cleanup_name))
                if rename_cleanup_error is not None:
                    self.merge_cleanup_result(
                        result,
                        self.classify_entry_by_expected(
                            name,
                            expected_state,
                            rename_cleanup_error,
                            exact_is_cleanup=False,
                        ),
                    )
                return result
            except OSError:
                self.merge_cleanup_result(
                    result,
                    self.classify_entry_by_expected(cleanup_name, expected_state, "OSError"),
                )
                if rename_cleanup_error is not None:
                    self.merge_cleanup_result(
                        result,
                        self.classify_entry_by_expected(
                            name,
                            expected_state,
                            rename_cleanup_error,
                            exact_is_cleanup=False,
                        ),
                    )
                return result
            finally:
                close_cleanup_handle()
        result.public_conflicts.append(self.evidence_path(cleanup_name))
        return result

    def move_target_to_backup(
        self,
        target_name: str,
        expected_state: CodexAgentFileState | None = None,
    ) -> str:
        self._validate_name(target_name)
        moved_name: str | None = None
        for _ in range(32):
            candidate = f".{target_name}.{secrets.token_hex(12)}.bak"
            try:
                codex_agent_windows_rename_no_replace(self, target_name, candidate)
                moved_name = candidate
                break
            except FileExistsError:
                continue
            except OSError as exc:
                result = CodexAgentCleanupResult()
                error = "backup_rename_failed"
                if isinstance(exc, CodexAgentWindowsRenameFailure) and exc.close_error is not None:
                    result.cleanup_errors.extend(self.close_handle_cleanup_errors_for_rename(exc))
                if isinstance(exc, CodexAgentWindowsRenameCommittedCloseFailure):
                    error = "backup_rename_close_failure"
                if expected_state is not None:
                    self.merge_cleanup_result(
                        result,
                        self.classify_entry_by_expected(candidate, expected_state, error),
                    )
                    self.merge_cleanup_result(
                        result,
                        self.classify_entry_by_expected(target_name, expected_state, error, exact_is_cleanup=False),
                    )
                else:
                    self.merge_cleanup_result(result, self.preserve_uncertain_entry(candidate, error))
                    self.merge_cleanup_result(result, self.preserve_uncertain_entry(target_name, error))
                if result:
                    raise CodexAgentNoClobberConflict(
                        "backup rename failed after possible commit",
                        result.preserved_paths,
                        result.cleanup_errors,
                    ) from exc
                raise
        if moved_name is None:
            raise OSError("could not allocate a collision-free backup name")
        return moved_name

    def preserve_state_as_backup(self, state: CodexAgentFileState, target_name: str) -> str:
        self._validate_name(target_name)
        preserved_name: str | None = None
        handle: int | None = None
        created = False
        primary_error: OSError | None = None
        close_errors: list[OSError] = []
        try:
            for _ in range(32):
                preserved_name = f".{target_name}.{secrets.token_hex(12)}.bak"
                try:
                    handle = self.open_child_handle(
                        preserved_name,
                        WINDOWS_GENERIC_READ | WINDOWS_GENERIC_WRITE,
                        0,
                        WINDOWS_CREATE_NEW,
                    )
                    created = True
                    break
                except FileExistsError:
                    preserved_name = None
            if handle is None or preserved_name is None:
                raise OSError("could not allocate exclusive anchored recovery copy")
            codex_agent_windows_write_all(handle, state.content)
            codex_agent_windows_set_mode_by_handle(handle, state.mode)
            codex_agent_windows_flush(handle)
            codex_agent_windows_seek_start(handle)
            restored = codex_agent_windows_read_all(handle)
            preserved_info = codex_agent_windows_file_info(handle)
            if preserved_info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT:
                raise OSError("preserved prior-state backup verification failed")
            if preserved_info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_DIRECTORY:
                raise OSError("preserved prior-state backup verification failed")
            if restored != state.content:
                raise OSError("preserved prior-state backup verification failed")
            expected_readonly = bool(codex_agent_windows_attributes_for_mode(state.mode) & WINDOWS_FILE_ATTRIBUTE_READONLY)
            actual_readonly = bool(preserved_info.dwFileAttributes & WINDOWS_FILE_ATTRIBUTE_READONLY)
            if actual_readonly != expected_readonly:
                raise OSError("preserved prior-state backup mode verification failed")
            if not self.is_current():
                raise OSError("destination moved before recovery-copy evidence")
        except OSError as exc:
            primary_error = exc
        finally:
            if handle is not None:
                codex_agent_record_close_error(close_errors, codex_agent_windows_close_handle(handle))
        if primary_error is not None or close_errors:
            failed_paths: list[str] = []
            if created and preserved_name is not None:
                failed_paths.append(self.evidence_path(preserved_name))
            preserved_paths: list[str] = []
            try:
                target_state = self.previous_state(target_name)
            except OSError:
                preserved_paths.append(self.evidence_path(target_name))
            else:
                if target_state is not None:
                    preserved_paths.append(self.evidence_path(target_name))
            detail = ""
            if close_errors:
                detail = f"; handle cleanup errors={len(close_errors)}"
            error = CodexAgentRecoveryCopyFailure(
                f"could not create a verified anchored recovery copy{detail}",
                failed_paths,
                preserved_paths,
            )
            if primary_error is not None:
                raise error from primary_error
            raise error from close_errors[0]
        if preserved_name is None:
            raise CodexAgentRecoveryCopyFailure("anchored recovery copy produced no result", [], [])
        return self.evidence_path(preserved_name)

    def open_child_handle(
        self,
        name: str,
        desired_access: int,
        share_mode: int,
        creation_disposition: int,
    ) -> int:
        self._validate_name(name)
        return codex_agent_windows_create_file(
            self.path(name),
            desired_access,
            share_mode,
            creation_disposition,
            WINDOWS_FILE_ATTRIBUTE_NORMAL | WINDOWS_FILE_FLAG_OPEN_REPARSE_POINT,
        )


class _AnchoredAgentDirScope:
    def __init__(self, destination: Path, identity: tuple[int, int] | None) -> None:
        self.destination = destination
        self.identity = identity
        self.agent_dir: AnchoredAgentDir | None = None
        self.owned = False
        self.close_errors: list[OSError] = []

    def __enter__(self) -> AnchoredAgentDir:
        active = codex_agent_current_anchored_directory(self.destination, self.identity)
        if active is not None:
            self.agent_dir = active
            return active
        self.agent_dir = AnchoredAgentDir.open(self.destination, self.identity)
        self.owned = True
        _CODEX_AGENT_ANCHORED_DIR_STACK.append(self.agent_dir)
        return self.agent_dir

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        if self.owned and self.agent_dir is not None:
            if _CODEX_AGENT_ANCHORED_DIR_STACK and _CODEX_AGENT_ANCHORED_DIR_STACK[-1] is self.agent_dir:
                _CODEX_AGENT_ANCHORED_DIR_STACK.pop()
            self.agent_dir.close(self.close_errors)
        return False


_CODEX_AGENT_ANCHORED_DIR_STACK: list[AnchoredAgentDir] = []


def codex_agent_current_anchored_directory(
    destination: Path,
    identity: tuple[int, int] | None,
) -> AnchoredAgentDir | None:
    if not _CODEX_AGENT_ANCHORED_DIR_STACK:
        return None
    active = _CODEX_AGENT_ANCHORED_DIR_STACK[-1]
    if active.matches(destination, identity):
        return active
    return None


def codex_agent_borrow_anchored_directory(
    destination: Path,
    identity: tuple[int, int] | None,
) -> _AnchoredAgentDirScope:
    return _AnchoredAgentDirScope(destination, identity)


def codex_agent_close_descriptor_nonmasking(descriptor: int) -> None:
    try:
        os.close(descriptor)
    except OSError:
        pass


def run_install_helper(entry: Any, request: Any) -> dict[str, Any]:
    if request.helper_id == "install-codex-agents":
        return run_codex_agent_install(entry, request)
    return run_doctor_helper(entry, request)


def run_codex_agent_install(entry: Any, request: Any) -> dict[str, Any]:
    source_dir = codex_plugin_root() / "codex-agents"
    source_result = load_codex_agent_bundle(source_dir, request.inputs)
    if is_diagnostic(source_result):
        return response("input_error", request_id=request.request_id, diagnostics=[source_result])
    rendered, model = source_result

    route_manifest: dict[str, Any] | None = None
    route_snapshot: dict[str, Any] | None = None
    strict_model_override = request.inputs.get("strict_model_override")
    if "route_policy_manifest" in request.inputs:
        if strict_model_override is not None and (not isinstance(strict_model_override, str) or not strict_model_override.strip()):
            return response(
                "input_error",
                request_id=request.request_id,
                diagnostics=[
                    diagnostic(
                        "invalid_strict_model_override",
                        "strict_model_override must be a non-empty model string",
                        remediation_summary="Use one explicit model string for strict route-aware override validation.",
                        remediation_actions=["Set inputs.strict_model_override to a supported manifest-admitted model."],
                    )
                ],
            )
        repo_root = find_repo_root(Path.cwd())
        if repo_root is None:
            return response(
                "missing_prerequisite",
                request_id=request.request_id,
                diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for route-aware Codex agent install")],
            )
        route_manifest = load_codex_route_policy_manifest(
            request.inputs.get("route_policy_manifest"),
            repo_root,
            source_dir,
        )
        if is_diagnostic(route_manifest):
            return response("input_error", request_id=request.request_id, diagnostics=[route_manifest])
        captured_snapshot = capture_codex_runtime_capabilities(request.inputs, route_manifest)
        if is_diagnostic(captured_snapshot):
            return response("input_error", request_id=request.request_id, diagnostics=[captured_snapshot])
        route_snapshot = normalize_codex_runtime_capability_snapshot(captured_snapshot, source="adapter")
        if is_diagnostic(route_snapshot):
            return response("input_error", request_id=request.request_id, diagnostics=[route_snapshot])

    destination_result = codex_agent_destination(request.inputs)
    if is_diagnostic(destination_result):
        return response("input_error", request_id=request.request_id, diagnostics=[destination_result])
    destination = destination_result
    unsafe = codex_agent_destination_diagnostic(destination)
    if unsafe is not None:
        return response("input_error", request_id=request.request_id, diagnostics=[unsafe])

    mutation = empty_mutation(request.mode)
    install_rendered = rendered
    route_routing: dict[str, Any] | None = None
    if route_manifest is not None and route_snapshot is not None:
        source_immutability_diag = codex_route_aware_source_immutability_diagnostic(source_dir, route_manifest)
        if source_immutability_diag is not None:
            return response("input_error", request_id=request.request_id, diagnostics=[source_immutability_diag])
        route_routing = codex_route_aware_adapter_routing(
            route_manifest,
            route_snapshot,
            mutation,
            source_dir,
            destination,
            request.inputs,
            strict_model_override=strict_model_override,
        )
        if codex_route_aware_has_required_miss(route_routing):
            mutation["mutation_status"] = "blocked"
            route_routing["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(
                mutation,
                no_mutation_reason="required_route_unresolved",
            )
            data = codex_agent_install_data(entry, request, mutation, source_dir, destination, model, install_rendered)
            data["routing"] = route_routing
            data["restart_required"] = False
            miss_diag = codex_route_aware_required_miss_diagnostic(route_routing)
            return response(
                "expected_failure",
                request_id=request.request_id,
                data=data,
                diagnostics=[miss_diag],
            )
        if codex_route_aware_has_unresolved_helper(route_routing):
            data = codex_agent_install_data(entry, request, mutation, source_dir, destination, model, install_rendered)
            data["routing"] = route_routing
            data["restart_required"] = False
            return response(
                "expected_failure",
                request_id=request.request_id,
                data=data,
                diagnostics=[codex_route_aware_helper_unresolved_diagnostic(route_routing)],
            )
        route_rendered = codex_route_aware_rendered_destination_bytes(route_routing, source_dir)
        if is_diagnostic(route_rendered):
            return response("input_error", request_id=request.request_id, diagnostics=[route_rendered])
        install_rendered = route_rendered

    planned: list[tuple[str, Path, bytes | None]] = []
    for name, content in install_rendered.items():
        target = destination / name
        operation = {"operation_id": f"install-codex-agent:{name}", "kind": "write_file", "target": target.as_posix()}
        try:
            previous_state = codex_agent_previous_state(target)
        except OSError as exc:
            return response(
                "input_error",
                request_id=request.request_id,
                diagnostics=[
                    diagnostic(
                        "unsafe_agent_destination",
                        "Codex agent destination contains an unsafe managed entry",
                        details={"path": target.as_posix(), "error": str(exc)},
                    )
                ],
            )
        current = previous_state.content if previous_state is not None else None
        if current == content:
            mutation["no_op_operations"].append(operation_record(operation))
            continue
        planned.append((name, target, content))
        mutation["planned_operations"].append(operation_record(operation))
        mutation["planned_paths"].append(target.as_posix())
    if route_routing is not None:
        helper_removal = codex_route_aware_helper_removal_action(route_routing, destination)
        if helper_removal is not None:
            name, target = helper_removal
            operation = {"operation_id": f"remove-codex-agent:{name}", "kind": "remove_file", "target": target.as_posix()}
            planned.append((name, target, None))
            mutation["planned_operations"].append(dict(operation))

    mutation["live_mutation"] = request.mode == "apply" and bool(planned)
    data = codex_agent_install_data(entry, request, mutation, source_dir, destination, model, install_rendered)
    if route_routing is not None:
        route_routing["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(mutation)
        data["routing"] = route_routing
    if request.mode == "dry_run":
        mutation["mutation_status"] = "planned" if planned else "no_op"
        return response("ok", request_id=request.request_id, data=data)

    if not planned:
        mutation["mutation_status"] = "no_op"
        data["restart_required"] = False
        data["verification"] = {"status": "verified", "matched_files": sorted(install_rendered)}
        if route_routing is not None:
            data["routing"]["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(mutation)
        return response("ok", request_id=request.request_id, data=data)

    if route_manifest is not None:
        source_immutability_diag = codex_route_aware_source_immutability_diagnostic(source_dir, route_manifest)
        if source_immutability_diag is not None:
            return response("input_error", request_id=request.request_id, data=data, diagnostics=[source_immutability_diag])

    previous: dict[str, CodexAgentFileState | None] = {}
    applied_previous: dict[str, CodexAgentFileState | None] = {}
    applied_states: dict[str, CodexAgentFileState | None] = {}
    destination_existed = destination.exists()
    destination_parent_existed = destination.parent.exists()
    destination_identity: tuple[int, int] | None = None
    destination_parent_identity: tuple[int, int] | None = None
    failed_name: str | None = None
    failed_operation: dict[str, Any] | None = None
    agent_dir_for_apply: AnchoredAgentDir | None = None
    final_anchor_cleanup_errors: list[dict[str, Any]] = []
    try:
        destination.mkdir(parents=True, exist_ok=True)
        unsafe = codex_agent_destination_diagnostic(destination)
        if unsafe is not None:
            raise OSError("destination changed before apply")
        if not destination_parent_existed:
            destination_parent_identity = codex_agent_destination_identity(destination.parent)
        destination_identity = codex_agent_destination_identity(destination)
        agent_dir_for_apply = AnchoredAgentDir.open(destination, destination_identity)
        _CODEX_AGENT_ANCHORED_DIR_STACK.append(agent_dir_for_apply)
        with codex_agent_borrow_anchored_directory(destination, destination_identity):
            for name, target, _content in planned:
                failed_name = name
                failed_operation = next(
                    (
                        dict(operation)
                        for operation in mutation["planned_operations"]
                        if isinstance(operation, dict)
                        and operation.get("operation_id")
                        in {f"install-codex-agent:{name}", f"remove-codex-agent:{name}"}
                    ),
                    None,
                )
                if not codex_agent_target_is_safe(target, destination, destination_identity):
                    raise OSError(f"unsafe destination entry: {name}")
                previous[name] = codex_agent_previous_state(target)
            for _index, (name, target, content) in enumerate(planned):
                failed_name = name
                failed_operation = next(
                    (
                        dict(operation)
                        for operation in mutation["planned_operations"]
                        if isinstance(operation, dict)
                        and operation.get("operation_id")
                        in {f"install-codex-agent:{name}", f"remove-codex-agent:{name}"}
                    ),
                    None,
                )
                if not codex_agent_target_is_safe(target, destination, destination_identity):
                    raise OSError(f"unsafe destination entry: {name}")
                if not codex_agent_state_matches(target, previous[name]):
                    raise OSError(f"destination entry changed after snapshot: {name}")
                if content is None:
                    if previous[name] is not None:
                        remove_codex_agent_if_unchanged(
                            target,
                            previous[name],
                            destination,
                            destination_identity,
                        )
                    operation = {"operation_id": f"remove-codex-agent:{name}", "kind": "remove_file", "target": target.as_posix()}
                else:
                    applied_state = write_codex_agent_atomic(
                        target,
                        content,
                        destination,
                        destination_identity,
                        expected_state=previous[name],
                    )
                    operation = {"operation_id": f"install-codex-agent:{name}", "kind": "write_file", "target": target.as_posix()}
                applied_previous[name] = previous[name]
                applied_states[name] = None if content is None else applied_state
                mutation["applied_operations"].append(dict(operation) if operation["kind"] == "remove_file" else operation_record(operation))
                mutation["touched_paths"].append(target.as_posix())

            failed_name = None
            failed_operation = None
            mismatches = verify_codex_agent_install(destination, install_rendered)
            if mismatches:
                failed_operation = {
                    "operation_id": "verify-codex-agent-install",
                    "kind": "verify_files",
                    "targets": [(destination / name).as_posix() for name in mismatches],
                }
                raise OSError(f"post-copy verification failed: {', '.join(mismatches)}")
    except OSError as exc:
        rollback_failures, rollback_cleanup_errors = rollback_codex_agent_install(
            destination,
            applied_previous,
            destination_identity,
            expected_current=applied_states,
        )
        if failed_name is not None and failed_name not in applied_states:
            failed_target = destination / failed_name
            if not codex_agent_state_matches(failed_target, previous.get(failed_name)):
                rollback_failures = sorted({*rollback_failures, failed_name})
        anchor_cleanup_errors: list[dict[str, Any]] = []
        if agent_dir_for_apply is not None:
            close_errors: list[OSError] = []
            close_kind = "close_handle" if isinstance(agent_dir_for_apply, WindowsAnchoredAgentDir) else "close_descriptor"
            if _CODEX_AGENT_ANCHORED_DIR_STACK and _CODEX_AGENT_ANCHORED_DIR_STACK[-1] is agent_dir_for_apply:
                _CODEX_AGENT_ANCHORED_DIR_STACK.pop()
            anchor_cleanup_errors.extend(agent_dir_for_apply.cleanup_errors)
            agent_dir_for_apply.close(close_errors)
            anchor_cleanup_errors.extend(
                {
                    "kind": close_kind,
                    "target": destination.as_posix(),
                    "error": type(error).__name__,
                }
                for error in close_errors
            )
            agent_dir_for_apply = None
        cleanup_actions, cleanup_errors = cleanup_codex_agent_destination(
            destination,
            destination_existed=destination_existed,
            destination_parent_existed=destination_parent_existed,
            destination_identity=destination_identity,
            destination_parent_identity=destination_parent_identity,
        )
        cleanup_errors = [*rollback_cleanup_errors, *anchor_cleanup_errors, *cleanup_errors]
        if isinstance(exc, CodexAgentNoClobberConflict):
            cleanup_errors.extend(exc.cleanup_errors)
            cleanup_errors.extend(
                codex_agent_unproven_preserved_path_records(
                    exc.preserved_paths,
                    cleanup_errors,
                    "no_clobber_conflict",
                )
            )
        elif isinstance(exc, CodexAgentRecoveryCopyFailure):
            cleanup_errors.extend(
                {
                    "kind": "recovery_copy_failed",
                    "target": path,
                    "error": "recovery_copy_incomplete",
                }
                for path in exc.failed_paths
            )
            cleanup_errors.extend(
                codex_agent_unproven_preserved_path_records(
                    exc.preserved_paths,
                    cleanup_errors,
                    "no_clobber_conflict",
                )
            )
        recovery_failed = bool(rollback_failures or cleanup_errors)
        mutation["mutation_status"] = "partial_failure" if recovery_failed else "blocked"
        mutation["failure_operation"] = failed_operation
        mutation["manual_remediation"] = [
            *codex_route_aware_rollback_manual_remediation(destination, rollback_failures),
            *codex_route_aware_cleanup_manual_remediation(cleanup_errors),
        ]
        data["verification"] = {"status": "failed", "matched_files": []}
        if route_routing is not None:
            recovery = codex_route_aware_recovery_after_apply_failure(
                mutation,
                destination,
                previous,
                applied_previous,
                rollback_failures,
                cleanup_actions,
                cleanup_errors,
            )
            data["routing"]["recovery_or_mutation"] = recovery
            data["writes_state"] = recovery["writes_state"]
            data["rollback_succeeded"] = not recovery_failed
            data["restart_required"] = recovery["restart_required"]
        else:
            data["writes_state"] = recovery_failed
            data["rollback_succeeded"] = not recovery_failed
            data["restart_required"] = recovery_failed
        return response(
            "expected_failure",
            request_id=request.request_id,
            data=data,
            diagnostics=[
                diagnostic(
                    "codex_agent_install_failed",
                    "Codex agent installation failed and rollback was attempted",
                    details={
                        "error": str(exc),
                        "rollback_failures": rollback_failures,
                        "cleanup_errors": cleanup_errors,
                    },
                    remediation_summary="Inspect the destination and retry after resolving the reported failure.",
                    remediation_actions=codex_route_aware_remediation_action_summaries(mutation["manual_remediation"])
                    or ["Retry the same request in dry_run mode."],
                )
            ],
        )
    finally:
        if agent_dir_for_apply is not None:
            close_errors: list[OSError] = []
            close_kind = "close_handle" if isinstance(agent_dir_for_apply, WindowsAnchoredAgentDir) else "close_descriptor"
            if _CODEX_AGENT_ANCHORED_DIR_STACK and _CODEX_AGENT_ANCHORED_DIR_STACK[-1] is agent_dir_for_apply:
                _CODEX_AGENT_ANCHORED_DIR_STACK.pop()
            final_anchor_cleanup_errors.extend(agent_dir_for_apply.cleanup_errors)
            agent_dir_for_apply.close(close_errors)
            final_anchor_cleanup_errors.extend(
                {
                    "kind": close_kind,
                    "target": destination.as_posix(),
                    "error": type(error).__name__,
                }
                for error in close_errors
            )
            agent_dir_for_apply = None

    if final_anchor_cleanup_errors:
        mutation["mutation_status"] = "partial_failure"
        mutation["manual_remediation"] = codex_route_aware_cleanup_manual_remediation(final_anchor_cleanup_errors)
        data["writes_state"] = True
        data["rollback_succeeded"] = False
        data["restart_required"] = True
        data["verification"] = {"status": "verified", "matched_files": sorted(install_rendered)}
        if route_routing is not None:
            data["routing"]["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(mutation)
        return response(
            "expected_failure",
            request_id=request.request_id,
            data=data,
            diagnostics=[
                diagnostic(
                    "codex_agent_install_failed",
                    "Codex agent installation completed but final anchored directory cleanup failed",
                    details={"cleanup_errors": final_anchor_cleanup_errors},
                    remediation_summary="Inspect the reported handle cleanup failure before treating the install as complete.",
                    remediation_actions=codex_route_aware_remediation_action_summaries(mutation["manual_remediation"])
                    or ["Retry after resolving the reported handle cleanup failure."],
                )
            ],
        )

    mutation["mutation_status"] = "applied"
    data["writes_state"] = True
    data["verification"] = {"status": "verified", "matched_files": sorted(install_rendered)}
    if route_routing is not None:
        data["routing"]["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(mutation)
    return response("ok", request_id=request.request_id, data=data)


def codex_route_aware_adapter_routing(
    route_manifest: dict[str, Any],
    route_snapshot: dict[str, Any],
    mutation: dict[str, Any],
    source_dir: Path,
    destination: Path,
    inputs: dict[str, Any],
    *,
    strict_model_override: Any = None,
) -> dict[str, Any]:
    required_agents = codex_route_aware_required_agents(
        route_manifest,
        route_snapshot,
        source_dir,
        strict_model_override=strict_model_override,
    )
    optional_helper_decision = codex_route_aware_optional_helper(
        route_manifest,
        route_snapshot,
        source_dir,
        destination,
        inputs,
        strict_model_override=strict_model_override,
    )
    return {
        "schema_version": "1.0",
        "mode": "route_aware",
        "manifest": {
            "path": route_manifest["path"],
            "manifest_id": route_manifest["manifest_id"],
            "schema_version": route_manifest["schema_version"],
            "source_roster_id": route_manifest["source_roster_id"],
            "provenance_id": route_manifest["provenance_id"],
        },
        "runtime_capability_snapshot": route_snapshot,
        "required_agents": required_agents,
        "optional_helper_decision": optional_helper_decision,
        "strict_override": codex_route_aware_strict_override_evidence(
            strict_model_override,
            required_agents,
            optional_helper_decision,
        ),
        "recovery_or_mutation": codex_route_aware_recovery_or_mutation(mutation),
    }


def codex_route_aware_required_agents(
    route_manifest: dict[str, Any],
    route_snapshot: dict[str, Any],
    source_dir: Path,
    *,
    strict_model_override: Any = None,
) -> list[dict[str, Any]]:
    policies = route_manifest["required_agent_policies"]
    records: list[dict[str, Any]] = []
    for agent_name in CODEX_REQUIRED_AGENT_NAMES:
        policy = policies[agent_name]
        records.append(
            codex_route_aware_resolve_agent(
                agent_name,
                policy,
                route_snapshot,
                source_dir,
                strict_model_override=strict_model_override if isinstance(strict_model_override, str) else None,
            )
        )
    return records


def codex_route_aware_optional_helper(
    route_manifest: dict[str, Any],
    route_snapshot: dict[str, Any],
    source_dir: Path,
    destination: Path,
    inputs: dict[str, Any],
    *,
    strict_model_override: Any = None,
) -> dict[str, Any]:
    policy = route_manifest["optional_helper_policy"]
    resolution = codex_route_aware_resolve_agent(
        CODEX_OPTIONAL_HELPER_NAME,
        policy,
        route_snapshot,
        source_dir,
        strict_model_override=strict_model_override if isinstance(strict_model_override, str) else None,
    )
    no_helper = policy.get("no_helper") if isinstance(policy.get("no_helper"), dict) else {}
    no_helper_validation = {
        "allowed": bool(no_helper.get("allowed")),
        "selected": False,
        "reason": no_helper.get("reason") if isinstance(no_helper.get("reason"), str) else None,
        "existing_helper_state": None,
    }
    managed_ownership_proof = None
    manual_remediation: list[dict[str, Any]] = []
    if resolution["terminal_outcome"] == "resolved":
        outcome = "installed"
    elif no_helper_validation["allowed"]:
        no_helper_validation["selected"] = True
        managed_ownership_proof = codex_route_aware_managed_helper_ownership_proof(
            route_manifest,
            source_dir,
            destination,
        )
        if managed_ownership_proof is None:
            preservation = codex_route_aware_unmanaged_helper_preservation(destination)
            if preservation is None:
                outcome = "omitted"
                no_helper_validation["existing_helper_state"] = "absent"
                managed_ownership_proof = {"status": "not_required", "reason": "helper_absent"}
            else:
                outcome = "preserved"
                no_helper_validation["existing_helper_state"] = "unmanaged"
                managed_ownership_proof = preservation["managed_ownership_proof"]
                manual_remediation = preservation["manual_remediation"]
        else:
            outcome = "removed"
            no_helper_validation["existing_helper_state"] = "managed"
    else:
        outcome = "unresolved"
        no_helper_validation["existing_helper_state"] = "unknown"
        managed_ownership_proof = None

    return {
        "helper_name": CODEX_OPTIONAL_HELPER_NAME,
        "outcome": outcome,
        "policy_id": resolution["policy_id"],
        "route_resolution_id": resolution["route_resolution_id"],
        "resolved_agent_policy_id": resolution["resolved_agent_policy_id"] if outcome == "installed" else None,
        "materialization_id": resolution["materialization_id"] if outcome == "installed" else None,
        "materialization_proof": resolution["materialization_proof"] if outcome == "installed" else None,
        "snapshot_id": resolution["snapshot_id"],
        "attempted_routes": resolution["attempted_routes"],
        "rejection_reasons": resolution["rejection_reasons"],
        "terminal_outcome": resolution["terminal_outcome"] if outcome == "installed" else outcome,
        "selected_route": resolution["selected_route"] if outcome == "installed" else None,
        "no_helper_validation": no_helper_validation,
        "managed_ownership_proof": managed_ownership_proof,
        "manual_remediation": manual_remediation,
    }


def codex_route_aware_resolve_agent(
    agent_name: str,
    policy: dict[str, Any],
    route_snapshot: dict[str, Any],
    source_dir: Path,
    *,
    strict_model_override: str | None = None,
) -> dict[str, Any]:
    snapshot_id = route_snapshot["snapshot_id"]
    attempted_routes: list[dict[str, Any]] = []
    rejection_reasons: list[str] = []
    selected_route: dict[str, Any] | None = None
    materialization_proof: dict[str, Any] | None = None
    materialization_failure: str | None = None

    routes = (
        [codex_route_aware_strict_override_route(policy, strict_model_override, agent_name=agent_name)]
        if strict_model_override is not None
        else codex_route_aware_policy_routes(policy)
    )
    for route in routes:
        normalized_route = codex_route_aware_normalize_route(route)
        rejection = (
            "strict_override_route_missing"
            if route.get("strict_override_missing") is True
            else codex_route_aware_route_rejection(policy, normalized_route, route_snapshot)
        )
        if rejection is None:
            try:
                materialization_proof = codex_route_aware_materialization_proof(source_dir, agent_name, normalized_route)
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError) as exc:
                materialization_failure = f"materialization_failed:{type(exc).__name__}"
                attempted_routes.append({**normalized_route, "outcome": "rejected", "reason": materialization_failure})
                rejection_reasons.append(f"{normalized_route['route_id']}: {materialization_failure}")
                continue
            attempted_routes.append({**normalized_route, "outcome": "selected"})
            selected_route = normalized_route
            break
        attempted_routes.append({**normalized_route, "outcome": "rejected", "reason": rejection})
        rejection_reasons.append(f"{normalized_route['route_id']}: {rejection}")

    route_resolution_id = route_policy_digest(
        {
            "agent_name": agent_name,
            "policy_id": policy.get("policy_id"),
            "snapshot_id": snapshot_id,
            "attempted_routes": attempted_routes,
            "selected_route": selected_route,
        }
    )
    if selected_route is None or materialization_proof is None:
        return {
            "agent_name": agent_name,
            "route_resolution_id": route_resolution_id,
            "policy_id": policy.get("policy_id"),
            "resolved_agent_policy_id": None,
            "materialization_id": None,
            "materialization_proof": None,
            "snapshot_id": snapshot_id,
            "attempted_routes": attempted_routes,
            "rejection_reasons": rejection_reasons,
            "selected_route": None,
            "terminal_outcome": materialization_failure or "unresolved",
        }

    resolved_agent_policy_id = route_policy_digest(
        {
            "agent_name": agent_name,
            "policy_id": policy.get("policy_id"),
            "selected_route": selected_route,
            "materialization_id": materialization_proof["materialization_id"],
            "non_route_contract_digest": policy.get("non_route_contract_digest"),
        }
    )
    return {
        "agent_name": agent_name,
        "route_resolution_id": route_resolution_id,
        "policy_id": policy.get("policy_id"),
        "resolved_agent_policy_id": resolved_agent_policy_id,
        "materialization_id": materialization_proof["materialization_id"],
        "materialization_proof": materialization_proof,
        "snapshot_id": snapshot_id,
        "attempted_routes": attempted_routes,
        "rejection_reasons": rejection_reasons,
        "selected_route": selected_route,
        "terminal_outcome": "resolved",
    }


def codex_route_aware_managed_helper_ownership_proof(
    route_manifest: dict[str, Any],
    source_dir: Path,
    destination: Path,
) -> dict[str, Any] | None:
    helper_target = destination / f"{CODEX_OPTIONAL_HELPER_NAME}.toml"
    try:
        existing_state = codex_agent_previous_state(helper_target)
    except OSError:
        return None
    if existing_state is None:
        return None

    existing_bytes = existing_state.content
    existing_digest = f"sha256:{hashlib.sha256(existing_bytes).hexdigest()}"
    known_digest = codex_route_aware_known_helper_rendered_digest(source_dir, route_manifest)
    if existing_digest == known_digest:
        return {
            "status": "known_rendered_digest",
            "helper_name": CODEX_OPTIONAL_HELPER_NAME,
            "existing_digest": existing_digest,
            "destination": helper_target.as_posix(),
            "known_rendered_digest": known_digest,
        }
    return None


def codex_route_aware_unmanaged_helper_preservation(destination: Path) -> dict[str, Any] | None:
    helper_target = destination / f"{CODEX_OPTIONAL_HELPER_NAME}.toml"
    try:
        existing_state = codex_agent_previous_state(helper_target)
    except OSError as exc:
        return {
            "managed_ownership_proof": {
                "status": "absent",
                "reason": "ownership_proof_absent",
                "helper_name": CODEX_OPTIONAL_HELPER_NAME,
                "destination": helper_target.as_posix(),
                "existing_digest": None,
                "read_error": type(exc).__name__,
            },
            "manual_remediation": [
                codex_route_aware_unmanaged_helper_manual_remediation(helper_target, read_error=type(exc).__name__)
            ],
        }
    if existing_state is None:
        return None

    existing_bytes = existing_state.content
    existing_digest = f"sha256:{hashlib.sha256(existing_bytes).hexdigest()}"
    return {
        "managed_ownership_proof": {
            "status": "absent",
            "reason": "ownership_proof_absent",
            "helper_name": CODEX_OPTIONAL_HELPER_NAME,
            "destination": helper_target.as_posix(),
            "existing_digest": existing_digest,
        },
        "manual_remediation": [codex_route_aware_unmanaged_helper_manual_remediation(helper_target)],
    }


def codex_route_aware_unmanaged_helper_manual_remediation(
    helper_target: Path,
    *,
    read_error: str | None = None,
) -> dict[str, Any]:
    action = {
        "action_type": "manual_remediation",
        "reason": "unmanaged_helper_preserved",
        "path": helper_target.as_posix(),
        "summary": "Existing same-named optional helper was preserved because managed ownership proof is absent.",
        "recommended_actions": [
            "Review the preserved helper file manually.",
            "Remove or rename it only after confirming it is not user-owned.",
        ],
    }
    if read_error is not None:
        action["read_error"] = read_error
    return action


def codex_route_aware_known_helper_rendered_digest(source_dir: Path, route_manifest: dict[str, Any]) -> str | None:
    policy = route_manifest["optional_helper_policy"]
    route = policy.get("preferred_route")
    if not isinstance(route, dict):
        return None
    try:
        rendered = codex_route_aware_render_destination_bytes(
            (source_dir / f"{CODEX_OPTIONAL_HELPER_NAME}.toml").read_bytes(),
            route,
            agent_name=CODEX_OPTIONAL_HELPER_NAME,
        )
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError):
        return None
    return f"sha256:{hashlib.sha256(rendered).hexdigest()}"


def codex_route_aware_helper_removal_action(routing: dict[str, Any], destination: Path) -> tuple[str, Path] | None:
    helper = routing.get("optional_helper_decision")
    if not isinstance(helper, dict) or helper.get("outcome") != "removed":
        return None
    name = f"{CODEX_OPTIONAL_HELPER_NAME}.toml"
    return name, destination / name


def codex_route_aware_policy_routes(policy: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    preferred = policy.get("preferred_route")
    if isinstance(preferred, dict):
        routes.append(preferred)
    fallbacks = policy.get("fallback_routes")
    if isinstance(fallbacks, list):
        routes.extend(route for route in fallbacks if isinstance(route, dict))
    return routes


def codex_route_aware_strict_override_route(policy: dict[str, Any], model: str, *, agent_name: str) -> dict[str, Any]:
    routes = codex_route_aware_policy_routes(policy)
    for route in routes:
        if route.get("model") == model:
            strict_route = dict(route)
            strict_route["route_id"] = f"strict-override:{agent_name}:{model}"
            strict_route["source_route_id"] = route["route_id"]
            return strict_route

    fallback = routes[0] if routes else {}
    return {
        "route_id": f"strict-override:{agent_name}:{model}",
        "model": model,
        "model_reasoning_effort": fallback.get("model_reasoning_effort") or "",
        "capabilities": list(fallback.get("capabilities") if isinstance(fallback.get("capabilities"), list) else []),
        "probe_id": fallback.get("probe_id"),
        "strict_override_missing": True,
    }


def codex_route_aware_normalize_route(route: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "route_id": route["route_id"],
        "model": route["model"],
        "model_reasoning_effort": route["model_reasoning_effort"],
        "capabilities": list(route["capabilities"]),
        "probe_id": route.get("probe_id"),
    }
    if isinstance(route.get("source_route_id"), str):
        normalized["source_route_id"] = route["source_route_id"]
    return normalized


def codex_route_aware_route_rejection(
    policy: dict[str, Any],
    route: dict[str, Any],
    route_snapshot: dict[str, Any],
) -> str | None:
    observation = route_snapshot.get("observation_evidence")
    available_routes = observation.get("available_routes") if isinstance(observation, dict) else []
    native_discovery = observation.get("native_discovery") if isinstance(observation, dict) else True
    availability_route_id = route.get("source_route_id") if isinstance(route.get("source_route_id"), str) else route["route_id"]
    observed_routes = set(available_routes if isinstance(available_routes, list) and native_discovery is not False else [])
    if availability_route_id not in observed_routes:
        if native_discovery is False and isinstance(route.get("probe_id"), str):
            probe_rejection = codex_route_aware_probe_route_rejection(route, route_snapshot, availability_route_id)
            if probe_rejection is not None:
                return probe_rejection
        else:
            return "route_unavailable"
    required_capabilities = policy.get("required_capabilities")
    if isinstance(required_capabilities, list) and not set(required_capabilities) <= set(route["capabilities"]):
        return "required_capability_missing"
    return None


def codex_route_aware_probe_route_rejection(
    route: dict[str, Any],
    route_snapshot: dict[str, Any],
    availability_route_id: str,
) -> str | None:
    probe_id = route.get("probe_id")
    child_results = route_snapshot.get("child_probe_results")
    if not isinstance(probe_id, str) or not isinstance(child_results, list):
        return "probe_result_missing"
    matches = [
        result
        for result in child_results
        if isinstance(result, dict)
        and result.get("probe_id") == probe_id
        and result.get("route_id") == availability_route_id
    ]
    if not matches:
        return "probe_result_missing"
    result = matches[0]
    status = result.get("status")
    available = result.get("available")
    if available is True and status in {"success", "available"}:
        return None
    if available is False or status in {"failed", "unavailable"}:
        return "probe_failed"
    return "probe_insufficient_result"


def codex_route_aware_strict_override_evidence(
    strict_model_override: Any,
    required_agents: list[dict[str, Any]],
    optional_helper_decision: dict[str, Any],
) -> dict[str, Any]:
    requested = isinstance(strict_model_override, str) and bool(strict_model_override.strip())
    if not requested:
        return {
            "requested": False,
            "status": "absent",
            "model": None,
            "evaluated_tuples": [],
            "required_agents_evaluated": 0,
            "helper_evaluated": False,
            "helper_tuple": None,
            "fallback_suppressed": False,
        }

    evaluated_tuples: list[dict[str, Any]] = []
    for record in required_agents:
        attempt = record["attempted_routes"][0] if record.get("attempted_routes") else {}
        evaluated_tuples.append(
            {
                "agent_name": record["agent_name"],
                "route_id": attempt.get("route_id"),
                "model": attempt.get("model"),
                "model_reasoning_effort": attempt.get("model_reasoning_effort"),
                "outcome": attempt.get("outcome"),
                "reason": attempt.get("reason"),
            }
        )
    compatible = all(record.get("terminal_outcome") == "resolved" for record in required_agents)
    helper_tuple = codex_route_aware_strict_helper_tuple(strict_model_override, optional_helper_decision)
    return {
        "requested": True,
        "status": "compatible" if compatible else "incompatible",
        "model": strict_model_override,
        "evaluated_tuples": evaluated_tuples,
        "required_agents_evaluated": len(required_agents),
        "helper_evaluated": True,
        "helper_tuple": helper_tuple,
        "fallback_suppressed": True,
    }


def codex_route_aware_strict_helper_tuple(
    strict_model_override: str,
    optional_helper_decision: dict[str, Any],
) -> dict[str, Any]:
    attempts = optional_helper_decision.get("attempted_routes")
    attempt = attempts[0] if isinstance(attempts, list) and attempts and isinstance(attempts[0], dict) else {}
    outcome = optional_helper_decision.get("outcome")
    if outcome == "installed":
        status = "compatible"
    elif outcome == "omitted" and optional_helper_decision.get("no_helper_validation", {}).get("selected") is True:
        status = "incompatible_no_helper"
    else:
        status = "unresolved"
    return {
        "helper_name": optional_helper_decision.get("helper_name"),
        "route_id": attempt.get("route_id"),
        "model": attempt.get("model", strict_model_override),
        "model_reasoning_effort": attempt.get("model_reasoning_effort"),
        "outcome": attempt.get("outcome"),
        "reason": attempt.get("reason"),
        "status": status,
    }


def codex_route_aware_materialization_proof(
    source_dir: Path,
    agent_name: str,
    selected_route: dict[str, Any],
) -> dict[str, Any]:
    source_path = source_dir / f"{agent_name}.toml"
    source_bytes = source_path.read_bytes()
    materialization = materialize_agent_policy(
        source_relative_path=f"speckit-pro/codex-agents/{agent_name}.toml",
        source_bytes=source_bytes,
        candidate_route={
            "agent_name": agent_name,
            "model": selected_route["model"],
            "model_reasoning_effort": selected_route["model_reasoning_effort"],
        },
    )
    return {
        "materialization_id": materialization.materialization_id,
        "source_path": materialization.source_binding["path"],
        "source_bytes_digest": materialization.source_binding["digest"],
        "destination_bytes_digest": materialization.destination_bytes_digest,
        "selected_model": materialization.selected_model,
        "selected_model_reasoning_effort": materialization.selected_model_reasoning_effort,
        "materializer_binding": materialization.materializer_binding,
        "non_route_fields_unchanged": materialization.non_route_fields_unchanged,
    }


def codex_route_aware_rendered_destination_bytes(routing: dict[str, Any], source_dir: Path) -> dict[str, bytes] | dict[str, Any]:
    rendered: dict[str, bytes] = {}
    try:
        for record in routing["required_agents"]:
            if record["terminal_outcome"] != "resolved" or not isinstance(record.get("selected_route"), dict):
                continue
            name = f"{record['agent_name']}.toml"
            rendered[name] = codex_route_aware_rendered_record_bytes(source_dir, record)

        helper = routing["optional_helper_decision"]
        if helper["outcome"] == "installed" and isinstance(helper.get("selected_route"), dict):
            rendered[f"{helper['helper_name']}.toml"] = codex_route_aware_rendered_record_bytes(source_dir, helper)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError, KeyError) as exc:
        return diagnostic(
            "codex_route_materialization_failed",
            "route-aware Codex agent plan could not render exact destination bytes",
            details={"error": type(exc).__name__, "message": str(exc)},
            remediation_summary="Inspect data.routing materialization records and retry with valid source TOMLs.",
            remediation_actions=["Restore the bundled Codex agent source files and rerun dry_run."],
        )

    missing_required = sorted(f"{agent}.toml" for agent in CODEX_REQUIRED_AGENT_NAMES if f"{agent}.toml" not in rendered)
    if missing_required:
        return diagnostic(
            "codex_route_materialization_failed",
            "route-aware Codex agent plan did not render every required destination file",
            details={"missing_required_files": missing_required},
            remediation_summary="Every required route must materialize before route-aware mutation planning.",
            remediation_actions=["Inspect data.routing.required_agents and fix unresolved route records."],
        )
    return rendered


def codex_route_aware_rendered_record_bytes(source_dir: Path, record: dict[str, Any]) -> bytes:
    agent_name = record["agent_name"] if "agent_name" in record else record["helper_name"]
    source_path = source_dir / f"{agent_name}.toml"
    rendered_bytes = codex_route_aware_render_destination_bytes(
        source_path.read_bytes(),
        record["selected_route"],
        agent_name=agent_name,
    )
    expected_digest = record["materialization_proof"]["destination_bytes_digest"]
    actual_digest = f"sha256:{hashlib.sha256(rendered_bytes).hexdigest()}"
    if actual_digest != expected_digest:
        raise ValueError("rendered bytes do not match materialization proof")
    return rendered_bytes


def codex_route_aware_render_destination_bytes(
    source_bytes: bytes,
    selected_route: dict[str, Any],
    *,
    agent_name: str,
) -> bytes:
    return materialize_agent_policy(
        source_relative_path=f"speckit-pro/codex-agents/{agent_name}.toml",
        source_bytes=source_bytes,
        candidate_route={
            "agent_name": agent_name,
            "model": selected_route["model"],
            "model_reasoning_effort": selected_route["model_reasoning_effort"],
        },
    ).destination_bytes


def codex_route_aware_source_immutability_diagnostic(source_dir: Path, route_manifest: dict[str, Any]) -> dict[str, Any] | None:
    roster = codex_agent_source_roster(source_dir)
    if is_diagnostic(roster):
        return roster
    if roster["source_roster_id"] != route_manifest["source_roster_id"]:
        return diagnostic(
            "codex_agent_source_changed",
            "bundled Codex agent source roster changed during route-aware install planning",
            details={
                "expected_source_roster_id": route_manifest["source_roster_id"],
                "actual_source_roster_id": roster["source_roster_id"],
            },
            remediation_summary="Retry from a stable plugin source bundle.",
            remediation_actions=["Restore the bundled Codex agent source files before applying route-aware installation."],
        )
    return None


def codex_route_aware_has_required_miss(routing: dict[str, Any]) -> bool:
    required_agents = routing.get("required_agents")
    if not isinstance(required_agents, list):
        return True
    return any(record.get("terminal_outcome") != "resolved" for record in required_agents if isinstance(record, dict))


def codex_route_aware_has_unresolved_helper(routing: dict[str, Any]) -> bool:
    helper = routing.get("optional_helper_decision")
    return isinstance(helper, dict) and helper.get("outcome") == "unresolved"


def codex_route_aware_required_miss_diagnostic(routing: dict[str, Any]) -> dict[str, Any]:
    strict = routing.get("strict_override") if isinstance(routing.get("strict_override"), dict) else {}
    if strict.get("status") == "incompatible":
        return diagnostic(
            "codex_strict_override_required_unresolved",
            "strict route-aware override could not resolve every required Codex agent",
            remediation_summary="Inspect data.routing.required_agents and strict_override.evaluated_tuples.",
            remediation_actions=["Retry with an override model that every required policy admits."],
        )
    return diagnostic(
        "codex_route_required_agent_unresolved",
        "route-aware Codex agent install could not resolve every required agent",
        remediation_summary="Inspect data.routing.required_agents and provide manifest-admitted available routes.",
        remediation_actions=["Retry with a compatible route-policy manifest and capability snapshot."],
    )


def codex_route_aware_helper_unresolved_diagnostic(routing: dict[str, Any]) -> dict[str, Any]:
    strict = routing.get("strict_override") if isinstance(routing.get("strict_override"), dict) else {}
    if strict.get("helper_tuple", {}).get("status") == "unresolved":
        return diagnostic(
            "codex_strict_override_helper_unresolved",
            "strict route-aware override could not resolve the optional helper or validate no-helper continuation",
            remediation_summary="Inspect data.routing.optional_helper_decision and strict_override.helper_tuple.",
            remediation_actions=["Permit validated no-helper continuation or use an override model compatible with the helper policy."],
        )
    return diagnostic(
        "codex_route_helper_unresolved",
        "route-aware Codex agent install could not resolve the optional helper or validate no-helper continuation",
        remediation_summary="Inspect data.routing.optional_helper_decision.",
        remediation_actions=["Provide a helper route or a validated no-helper policy."],
    )


def codex_route_aware_recovery_or_mutation(
    mutation: dict[str, Any],
    *,
    no_mutation_reason: str | None = None,
) -> dict[str, Any]:
    planned_operations = mutation.get("planned_operations", [])
    applied_operations = mutation.get("applied_operations", [])
    planned_writes = list(mutation.get("planned_paths", []))
    planned_removals = [
        operation["target"]
        for operation in planned_operations
        if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
    ]
    applied_removals = [
        operation["target"]
        for operation in applied_operations
        if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
    ]
    touched_paths = list(mutation.get("touched_paths", []))
    applied_writes = [path for path in touched_paths if path not in set(applied_removals)]
    writes_state = bool(applied_writes or applied_removals)
    terminal_outcome = "planned" if (planned_writes or planned_removals) and not (applied_writes or applied_removals) else "no_mutation"
    state_identity = route_policy_digest(
        {
            "terminal_outcome": terminal_outcome,
            "planned_writes": planned_writes,
            "planned_removals": planned_removals,
            "applied_writes": applied_writes,
            "applied_removals": applied_removals,
            "writes_state": writes_state,
        }
    )
    final_state_identity = (
        state_identity
        if not writes_state
        else route_policy_digest(
            {
                "terminal_outcome": terminal_outcome,
                "applied_writes": applied_writes,
                "applied_removals": applied_removals,
                "writes_state": writes_state,
            }
        )
    )
    return {
        "planned_writes": planned_writes,
        "planned_removals": planned_removals,
        "applied_writes": applied_writes,
        "applied_removals": applied_removals,
        "recovery_record": {
            "pre_state_id": state_identity,
            "final_state_id": final_state_identity,
            "staged_actions": list(planned_operations if isinstance(planned_operations, list) else []),
            "applied_actions": list(applied_operations if isinstance(applied_operations, list) else []),
            "rolled_back_actions": [],
            "cleanup_actions": [],
            "cleanup_errors": [],
            "failed_actions": [],
            "rollback_outcome": "not_required",
            "manual_remediation": [],
            "terminal_outcome": terminal_outcome,
            "no_mutation_reason": no_mutation_reason if terminal_outcome == "no_mutation" else None,
        },
        "writes_state": writes_state,
        "restart_required": writes_state,
    }


def codex_route_aware_recovery_after_apply_failure(
    mutation: dict[str, Any],
    destination: Path,
    previous: dict[str, CodexAgentFileState | None],
    applied_previous: dict[str, CodexAgentFileState | None],
    rollback_failures: list[str],
    cleanup_actions: list[dict[str, Any]],
    cleanup_errors: list[dict[str, Any]],
) -> dict[str, Any]:
    planned_operations = mutation.get("planned_operations", [])
    applied_operations = mutation.get("applied_operations", [])
    applied_removals = [
        operation["target"]
        for operation in applied_operations
        if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
    ]
    touched_paths = list(mutation.get("touched_paths", []))
    applied_writes = [path for path in touched_paths if path not in set(applied_removals)]
    prior_state = codex_route_aware_state_records(destination, previous)
    final_state = codex_route_aware_destination_state_records(destination, list(previous))
    pre_state_id = route_policy_digest(prior_state)
    final_state_id = route_policy_digest(final_state)
    writes_state = bool(rollback_failures or cleanup_errors) or pre_state_id != final_state_id
    rollback_outcome = "unrestored" if rollback_failures or pre_state_id != final_state_id else "restored"
    failure_operation = mutation.get("failure_operation")
    rollback_error_records = codex_route_aware_rollback_error_records(destination, rollback_failures)
    unrestored_actions = codex_route_aware_unrestored_actions(destination, rollback_failures)
    terminal_outcome = "uncertain_state" if writes_state else "restored"
    return {
        "planned_writes": list(mutation.get("planned_paths", [])),
        "planned_removals": [
            operation["target"]
            for operation in planned_operations
            if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
        ],
        "applied_writes": applied_writes,
        "applied_removals": applied_removals,
        "recovery_record": {
            "pre_state_id": pre_state_id,
            "final_state_id": final_state_id,
            "prior_state": prior_state,
            "final_state": final_state,
            "staged_actions": list(planned_operations if isinstance(planned_operations, list) else []),
            "applied_actions": list(applied_operations if isinstance(applied_operations, list) else []),
            "rolled_back_actions": codex_route_aware_rolled_back_actions(
                destination,
                applied_previous,
                rollback_failures,
            ),
            "cleanup_actions": list(cleanup_actions),
            "cleanup_errors": list(cleanup_errors),
            "failed_actions": codex_route_aware_failed_actions(destination, failure_operation),
            "rollback_outcome": rollback_outcome,
            "rollback_failures": list(rollback_failures),
            "rollback_errors": rollback_error_records,
            "unrestored_actions": unrestored_actions,
            "state_status": "uncertain" if writes_state else "restored",
            "manual_remediation": list(mutation.get("manual_remediation", [])),
            "terminal_outcome": terminal_outcome,
            "no_mutation_reason": None,
        },
        "writes_state": writes_state,
        "restart_required": writes_state,
    }


def codex_route_aware_state_records(
    destination: Path,
    states: dict[str, CodexAgentFileState | None],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, state in states.items():
        records.append(codex_route_aware_state_record(destination / name, name, state))
    return records


def codex_route_aware_destination_state_records(destination: Path, names: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name in names:
        target = destination / name
        try:
            state = codex_agent_previous_state(target)
        except OSError as exc:
            records.append(
                {
                    "name": name,
                    "target": target.as_posix(),
                    "existed": "unknown",
                    "digest": None,
                    "mode": None,
                    "error": type(exc).__name__,
                }
            )
            continue
        records.append(codex_route_aware_state_record(target, name, state))
    return records


def codex_route_aware_state_record(
    target: Path,
    name: str,
    state: CodexAgentFileState | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": name,
        "target": target.as_posix(),
        "existed": state is not None,
        "digest": None,
        "mode": None,
    }
    if state is not None:
        record["digest"] = f"sha256:{hashlib.sha256(state.content).hexdigest()}"
        record["mode"] = oct(state.mode & 0o7777)
    return record


def codex_route_aware_rolled_back_actions(
    destination: Path,
    previous: dict[str, CodexAgentFileState | None],
    rollback_failures: list[str],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    failed_names = set(rollback_failures)
    for name, state in previous.items():
        if name in failed_names:
            continue
        actions.append(
            {
                "operation_id": f"rollback-codex-agent:{name}",
                "kind": "restore_file" if state is not None else "remove_file",
                "name": name,
                "target": (destination / name).as_posix(),
            }
        )
    return actions


def codex_route_aware_failed_actions(destination: Path, failure_operation: Any) -> list[dict[str, Any]]:
    if not isinstance(failure_operation, dict):
        return []
    operation_id = failure_operation.get("operation_id")
    if not isinstance(operation_id, str):
        return [dict(failure_operation)]
    name = operation_id.removeprefix("install-codex-agent:")
    if name == operation_id:
        name = operation_id.removeprefix("remove-codex-agent:")
    if name == operation_id:
        return [dict(failure_operation)]
    return [
        {
            **failure_operation,
            "name": name,
            "target": (destination / name).as_posix(),
        }
    ]


def codex_route_aware_rollback_error_records(
    destination: Path,
    rollback_failures: list[str],
) -> list[dict[str, Any]]:
    return [{"name": name, "target": (destination / name).as_posix(), "error": "OSError"} for name in rollback_failures]


def codex_route_aware_unrestored_actions(
    destination: Path,
    rollback_failures: list[str],
) -> list[dict[str, Any]]:
    return [{"name": name, "target": (destination / name).as_posix()} for name in rollback_failures]


def codex_route_aware_rollback_manual_remediation(
    destination: Path,
    rollback_failures: list[str],
) -> list[dict[str, Any]]:
    if not rollback_failures:
        return []
    paths = [(destination / name).as_posix() for name in rollback_failures]
    return [
        {
            "action_type": "manual_remediation",
            "reason": "rollback_unrestored",
            "paths": paths,
            "summary": "Restart Codex after manually restoring or reviewing unrestored agent files.",
            "recommended_actions": [
                "Restore each unrestored file from the previous known-good bytes when available.",
                "Review the route-aware recovery record before retrying apply.",
                "Restart Codex after correcting the reported destination state.",
            ],
        }
    ]


def codex_route_aware_cleanup_manual_remediation(
    cleanup_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    directory_paths = [
        error["target"]
        for error in cleanup_errors
        if error.get("kind") == "remove_directory" and isinstance(error.get("target"), str)
    ]
    preserved_paths = [
        error["target"]
        for error in cleanup_errors
        if error.get("kind") == "preserved_concurrent_file" and isinstance(error.get("target"), str)
    ]
    retained_cleanup_paths = [
        error["target"]
        for error in cleanup_errors
        if error.get("kind") in {"preserved_cleanup_entry", "cleanup_incomplete"} and isinstance(error.get("target"), str)
    ]
    failed_copy_paths = [
        error["target"]
        for error in cleanup_errors
        if error.get("kind") == "recovery_copy_failed" and isinstance(error.get("target"), str)
    ]
    actions: list[dict[str, Any]] = []
    if directory_paths or retained_cleanup_paths:
        actions.append({
            "action_type": "manual_remediation",
            "reason": "cleanup_incomplete",
            "paths": [*directory_paths, *retained_cleanup_paths],
            "summary": "Inspect retained installer cleanup entries and remove them only after confirming the intended state.",
            "recommended_actions": [
                "Inspect each reported cleanup path without following symlinks.",
                "Remove only installer-created cleanup residue whose bytes are no longer needed.",
                "Retry the install after the destination state is understood.",
            ],
        })
    if preserved_paths:
        actions.append({
            "action_type": "manual_remediation",
            "reason": "concurrent_file_preserved",
            "paths": preserved_paths,
            "summary": "Inspect preserved unknown/private concurrent data and keep the intended version before retrying.",
            "recommended_actions": [
                "Compare the reported target and backup bytes without following symlinks.",
                "Keep or restore unknown/private concurrent data before removing any installer cleanup residue.",
                "Retry only after the destination has stopped changing.",
            ],
        })
    if failed_copy_paths:
        actions.append({
            "action_type": "manual_remediation",
            "reason": "recovery_copy_failed",
            "paths": failed_copy_paths,
            "summary": "Recovery could not verify an exact prior-state backup; inspect the target and any incomplete copy before retrying.",
            "recommended_actions": [
                "Treat each reported recovery copy as incomplete, not as a valid prior-state backup.",
                "Inspect content and mode without following symlinks, then restore the intended known-good state.",
                "Retry only after the destination identity and file state are stable.",
            ],
        })
    return actions


def codex_route_aware_remediation_action_summaries(raw_actions: Any) -> list[str]:
    if not isinstance(raw_actions, list):
        return []
    summaries: list[str] = []
    for action in raw_actions:
        if isinstance(action, str):
            summaries.append(action)
        elif isinstance(action, dict) and isinstance(action.get("summary"), str):
            summaries.append(action["summary"])
    return summaries


def load_codex_agent_bundle(source_dir: Path, inputs: dict[str, Any]) -> tuple[dict[str, bytes], str] | dict[str, Any]:
    raw_model = inputs["model"] if "model" in inputs else os.environ.get("SPECKIT_CODEX_MODEL") or CODEX_SOL_SOURCE_MODEL
    if not isinstance(raw_model, str) or raw_model not in SUPPORTED_CODEX_AGENT_MODELS:
        return diagnostic(
            "unsupported_codex_model",
            "model must be gpt-6-sol, gpt-6-luna, or gpt-6-astra",
            details={"model": raw_model},
            remediation_summary="Choose a supported explicit Codex agent model.",
            remediation_actions=["Set inputs.model to gpt-6-sol (default), gpt-6-luna, or gpt-6-astra."],
        )
    if "luna_fallback" in inputs:
        luna_fallback = inputs["luna_fallback"]
    else:
        env_fallback = os.environ.get("SPECKIT_CODEX_LUNA_FALLBACK")
        luna_fallback = {None: False, "": False, "false": False, "true": True}.get(env_fallback, env_fallback)
    if not isinstance(luna_fallback, bool):
        return diagnostic(
            "invalid_luna_fallback",
            "luna_fallback must be true or false",
            details={"luna_fallback": luna_fallback},
            remediation_summary="Use a boolean to choose whether Luna roles fall back to gpt-6-sol.",
            remediation_actions=[
                "Set inputs.luna_fallback or SPECKIT_CODEX_LUNA_FALLBACK to true only when gpt-6-luna is unavailable."
            ],
        )
    if luna_fallback and raw_model == CODEX_LUNA_SOURCE_MODEL:
        return diagnostic(
            "conflicting_luna_fallback",
            "luna_fallback cannot be combined with model gpt-6-luna",
            details={"model": raw_model, "luna_fallback": luna_fallback},
            remediation_summary="The Luna fallback exists for environments where gpt-6-luna is unavailable.",
            remediation_actions=["Use model gpt-6-sol or gpt-6-astra with luna_fallback, or omit luna_fallback."],
        )
    roster_result = codex_agent_source_roster(source_dir)
    if is_diagnostic(roster_result):
        return roster_result
    source_files = sorted(source_dir.glob("*.toml"), key=lambda path: path.name)
    rendered: dict[str, bytes] = {}
    try:
        for path in source_files:
            if path.is_symlink() or not path.is_file():
                raise OSError(path.name)
            source_bytes = path.read_bytes()
            source_text = source_bytes.decode("utf-8")
            source_policy = tomllib.loads(source_text)
            if source_policy.get("name") != path.stem:
                raise ValueError(f"{path.name}: name must match filename")
            if path.stem not in CODEX_SOURCE_AGENT_POLICIES:
                raise ValueError(f"{path.name}: no inventory policy")
            expected_source_model, expected_source_effort = CODEX_SOURCE_AGENT_POLICIES[path.stem]
            if source_policy.get("model") != expected_source_model:
                raise ValueError(f"{path.name}: unexpected source model")
            if source_policy.get("model_reasoning_effort") != expected_source_effort:
                raise ValueError(f"{path.name}: unexpected source reasoning effort")

            if expected_source_model == CODEX_SOL_SOURCE_MODEL:
                target_model = raw_model
            elif expected_source_model == CODEX_LUNA_SOURCE_MODEL and luna_fallback:
                target_model = CODEX_LUNA_FALLBACK_MODEL
            else:
                target_model = expected_source_model
            if target_model != expected_source_model:
                rendered_text, replacement_count = re.subn(
                    rf'^model = "{re.escape(expected_source_model)}"$',
                    f'model = "{target_model}"',
                    source_text,
                    flags=re.MULTILINE,
                )
                if replacement_count != 1:
                    raise ValueError(f"{path.name}: expected exactly one model rewrite")
                rendered_policy = tomllib.loads(rendered_text)
                if rendered_policy.get("model") != target_model:
                    raise ValueError(f"{path.name}: model rewrite did not validate")
                rendered[path.name] = rendered_text.encode("utf-8")
            else:
                rendered[path.name] = source_bytes
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError) as exc:
        return diagnostic(
            "unsafe_agent_bundle",
            "bundled Codex agent templates could not be read safely",
            details={"error": type(exc).__name__, "message": str(exc)},
        )
    return rendered, raw_model


def codex_agent_destination(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    default = Path.home() / ".codex" / "agents"
    raw = inputs.get("destination")
    if raw is None:
        candidate = default
    elif not isinstance(raw, str) or not raw.strip():
        return diagnostic("invalid_destination", "destination must be a non-empty path string")
    else:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
    candidate = candidate.absolute()
    allowed = {
        default.absolute(),
        (Path.cwd() / ".codex" / "agents").absolute(),
    }
    if candidate not in allowed:
        return diagnostic(
            "invalid_destination",
            "destination must be the user or current-project Codex agents directory",
            details={"destination": candidate.as_posix()},
            remediation_summary="Use ~/.codex/agents or .codex/agents.",
            remediation_actions=["Retry with a Codex-native agent destination."],
        )
    return candidate


def codex_agent_destination_diagnostic(destination: Path) -> dict[str, Any] | None:
    for path in (destination, *destination.parents):
        if path.exists() and path.is_symlink():
            return diagnostic(
                "unsafe_agent_destination",
                "Codex agent destination must not traverse symlinks",
                details={"path": path.as_posix()},
            )
        if path == path.parent:
            break
    if destination.exists() and not destination.is_dir():
        return diagnostic("unsafe_agent_destination", "Codex agent destination is not a directory")
    return None


def codex_agent_destination_identity(destination: Path) -> tuple[int, int]:
    metadata = destination.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise OSError("destination is not a stable directory")
    return metadata.st_dev, metadata.st_ino


def codex_agent_previous_state(target: Path) -> CodexAgentFileState | None:
    active = codex_agent_current_anchored_directory(target.parent, None)
    if active is not None:
        return active.previous_state(target.name)
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise OSError("managed target is not a regular file")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(target, flags)
        opened_metadata = os.fstat(descriptor)
        if (opened_metadata.st_dev, opened_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise OSError("managed target changed while being read")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = None
            content = handle.read()
            opened_metadata = os.fstat(handle.fileno())
            if (opened_metadata.st_dev, opened_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
                raise OSError("managed target changed while being read")
    finally:
        if descriptor is not None:
            codex_agent_close_descriptor_nonmasking(descriptor)
    return CodexAgentFileState(
        content=content,
        mode=opened_metadata.st_mode,
        device=opened_metadata.st_dev,
        inode=opened_metadata.st_ino,
    )


def codex_agent_state_matches(target: Path, expected: CodexAgentFileState | None) -> bool:
    try:
        return codex_agent_previous_state(target) == expected
    except OSError:
        return False


def rollback_codex_agent_install(
    destination: Path,
    previous: dict[str, CodexAgentFileState | None],
    destination_identity: tuple[int, int] | None,
    *,
    expected_current: dict[str, CodexAgentFileState | None],
) -> tuple[list[str], list[dict[str, str]]]:
    failures: list[str] = []
    cleanup_errors: list[dict[str, str]] = []
    for name, state in reversed(list(previous.items())):
        target = destination / name
        try:
            if not codex_agent_state_matches(target, expected_current[name]):
                raise OSError("rollback target changed after installer mutation")
            if state is None:
                if not codex_agent_target_is_safe(target, destination, destination_identity):
                    raise OSError("rollback target became unsafe")
                if target.exists():
                    remove_codex_agent_if_unchanged(
                        target,
                        expected_current[name],
                        destination,
                        destination_identity,
                    )
            else:
                write_codex_agent_atomic(
                    target,
                    state.content,
                    destination,
                    destination_identity,
                    mode=state.mode,
                    expected_state=expected_current[name],
                    cleanup_race_state=state,
                )
        except CodexAgentNoClobberConflict as exc:
            failures.append(name)
            cleanup_errors.extend(exc.cleanup_errors)
            cleanup_errors.extend(
                codex_agent_unproven_preserved_path_records(
                    exc.preserved_paths,
                    cleanup_errors,
                    "no_clobber_conflict",
                )
            )
        except CodexAgentRecoveryCopyFailure as exc:
            failures.append(name)
            cleanup_errors.extend(
                {
                    "kind": "recovery_copy_failed",
                    "target": path,
                    "error": "recovery_copy_incomplete",
                }
                for path in exc.failed_paths
            )
            cleanup_errors.extend(
                codex_agent_unproven_preserved_path_records(
                    exc.preserved_paths,
                    cleanup_errors,
                    "no_clobber_conflict",
                )
            )
        except OSError:
            failures.append(name)
    return sorted(failures), cleanup_errors


def cleanup_codex_agent_destination(
    destination: Path,
    *,
    destination_existed: bool,
    destination_parent_existed: bool,
    destination_identity: tuple[int, int] | None = None,
    destination_parent_identity: tuple[int, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cleanup_actions: list[dict[str, Any]] = []
    cleanup_errors: list[dict[str, Any]] = []
    for path, existed, identity in (
        (destination, destination_existed, destination_identity),
        (destination.parent, destination_parent_existed, destination_parent_identity),
    ):
        if existed:
            continue
        if identity is not None:
            action, error = codex_agent_remove_directory_identity_bound(path, identity)
            if action is not None:
                cleanup_actions.append(action)
                continue
            if error is not None:
                cleanup_errors.append(error)
                break
            continue
        try:
            path.rmdir()
            cleanup_actions.append({"kind": "remove_directory", "target": path.as_posix()})
        except OSError as exc:
            # Cleanup is best-effort and must not replace the install or rollback result.
            if path.exists():
                cleanup_errors.append(
                    {"kind": "remove_directory", "target": path.as_posix(), "error": type(exc).__name__}
                )
    return cleanup_actions, cleanup_errors


def codex_agent_remove_directory_identity_bound(
    path: Path,
    expected_identity: tuple[int, int],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        current_identity = codex_agent_destination_identity(path)
    except OSError as exc:
        if path.exists():
            return None, {"kind": "remove_directory", "target": path.as_posix(), "error": type(exc).__name__}
        return None, None
    if current_identity != expected_identity:
        return None, {"kind": "remove_directory", "target": path.as_posix(), "error": "destination_identity_mismatch"}

    quarantine: Path | None = None
    for _ in range(32):
        candidate = path.parent / f".{path.name}.{secrets.token_hex(12)}.cleanup-dir"
        if candidate.exists():
            continue
        quarantine = candidate
        break
    if quarantine is None:
        return None, {"kind": "remove_directory", "target": path.as_posix(), "error": "cleanup_name_unavailable"}

    try:
        codex_agent_rename_path_no_replace(path, quarantine)
    except FileExistsError:
        return None, {"kind": "remove_directory", "target": quarantine.as_posix(), "error": "cleanup_name_conflict"}
    except OSError as exc:
        if path.exists():
            return None, {"kind": "remove_directory", "target": path.as_posix(), "error": type(exc).__name__}
        return None, None

    try:
        quarantine_identity = codex_agent_destination_identity(quarantine)
    except OSError as exc:
        return None, {"kind": "remove_directory", "target": quarantine.as_posix(), "error": type(exc).__name__}
    if quarantine_identity != expected_identity:
        return None, {"kind": "remove_directory", "target": quarantine.as_posix(), "error": "destination_identity_mismatch"}

    return None, {
        "kind": "remove_directory",
        "target": quarantine.as_posix(),
        "error": "identity_bound_directory_removal_unavailable",
    }


def write_codex_agent_atomic(
    target: Path,
    content: bytes,
    destination: Path,
    destination_identity: tuple[int, int] | None,
    *,
    mode: int | None = None,
    expected_state: CodexAgentFileState | None | object = CODEX_AGENT_STATE_UNSET,
    cleanup_race_state: CodexAgentFileState | None = None,
) -> CodexAgentFileState:
    if destination_identity is None:
        destination_identity = codex_agent_destination_identity(destination)
    with codex_agent_borrow_anchored_directory(destination, destination_identity) as agent_dir:
        if target.parent != destination or not agent_dir.target_is_safe(target.name):
            raise OSError("unsafe target path")
        tmp_name: str | None = None
        backup_name: str | None = None
        prepared_state: CodexAgentFileState | None = None
        moved_state: CodexAgentFileState | None = None
        try:
            tmp_name = agent_dir.create_temp_file(target.name, content, mode)
            prepared_state = agent_dir.previous_state(tmp_name)
            if prepared_state is None:
                raise OSError("temporary install file disappeared")
            agent_dir.ensure_current("destination changed after temporary file creation")
            if not agent_dir.target_is_safe(target.name):
                raise OSError("target path changed before no-clobber install")
            if expected_state is CODEX_AGENT_STATE_UNSET:
                expected_state = agent_dir.previous_state(target.name)
            if expected_state is not None:
                backup_name = agent_dir.move_target_to_backup(
                    target.name,
                    expected_state if isinstance(expected_state, CodexAgentFileState) else None,
                )
                moved_state = agent_dir.previous_state(backup_name)
                if moved_state != expected_state:
                    try:
                        agent_dir.restore_backup_no_clobber(backup_name, target.name)
                    except OSError as restore_exc:
                        preserved_paths: list[str] = []
                        cleanup_errors: list[dict[str, str]] = []
                        agent_dir.restore_failure_for_packaging(
                            restore_exc,
                            backup_name,
                            target.name,
                            preserved_paths,
                            cleanup_errors,
                            "secondary_restore_failure",
                        )
                        backup_name = None
                        raise CodexAgentNoClobberConflict(
                            "target changed before no-clobber install",
                            list(dict.fromkeys(preserved_paths)),
                            cleanup_errors,
                        ) from restore_exc
                    backup_name = None
                    raise OSError("target changed before no-clobber install")
            elif agent_dir.previous_state(target.name) is not None:
                raise OSError("target appeared before no-clobber install")
            try:
                agent_dir.rename_no_replace(tmp_name, target.name)
                tmp_name = None
            except OSError as link_exc:
                if isinstance(link_exc, CodexAgentWindowsRenameFailure) and prepared_state is not None:
                    result = CodexAgentCleanupResult()
                    error = "publish_rename_failed"
                    if link_exc.close_error is not None:
                        result.cleanup_errors.extend(agent_dir.close_handle_cleanup_errors_for_rename(link_exc))
                    if isinstance(link_exc, CodexAgentWindowsRenameCommittedCloseFailure):
                        error = "publish_rename_close_failure"
                    agent_dir.merge_cleanup_result(
                        result,
                        agent_dir.classify_entry_by_expected(
                            target.name,
                            prepared_state,
                            error,
                            exact_is_cleanup=False,
                        ),
                    )
                    raise CodexAgentNoClobberConflict(
                        "target publish close failed"
                        if isinstance(link_exc, CodexAgentWindowsRenameCommittedCloseFailure)
                        else "target publish failed",
                        result.preserved_paths,
                        result.cleanup_errors,
                    ) from link_exc
                result = CodexAgentCleanupResult()
                if prepared_state is not None:
                    agent_dir.merge_cleanup_result(
                        result,
                        agent_dir.classify_entry_by_expected(
                            target.name,
                            prepared_state,
                            "publish_rename_failed",
                            exact_is_cleanup=False,
                        ),
                    )
                if isinstance(link_exc, CodexAgentNoClobberConflict):
                    result.public_conflicts = [*link_exc.preserved_paths, *result.public_conflicts]
                    result.cleanup_errors = [*link_exc.cleanup_errors, *result.cleanup_errors]
                if backup_name is not None:
                    result.public_conflicts.insert(0, agent_dir.evidence_path(backup_name))
                raise CodexAgentNoClobberConflict(
                    "target changed during no-clobber install",
                    result.preserved_paths,
                    result.cleanup_errors,
                ) from None
            try:
                installed_state = agent_dir.previous_state(target.name)
            except OSError as read_exc:
                paths = [agent_dir.evidence_path(target.name)]
                cleanup_errors = [
                    agent_dir.preserved_concurrent_file(
                        agent_dir.evidence_path(target.name),
                        "secondary_target_read_failure",
                    )
                ]
                if backup_name is not None:
                    paths.insert(0, agent_dir.evidence_path(backup_name))
                raise CodexAgentNoClobberConflict(
                    "target changed during no-clobber install",
                    paths,
                    cleanup_errors,
                ) from read_exc
            if installed_state != prepared_state:
                paths = [agent_dir.evidence_path(target.name)]
                if backup_name is not None:
                    paths.insert(0, agent_dir.evidence_path(backup_name))
                raise CodexAgentNoClobberConflict("target changed after no-clobber link", paths)
            if isinstance(agent_dir, WindowsAnchoredAgentDir) and mode is not None:
                installed_state = agent_dir.apply_child_mode_verified(target.name, mode, prepared_state)
                prepared_state = installed_state
            agent_dir.ensure_current("destination changed during no-clobber install")
            if not agent_dir.state_matches(target.name, prepared_state):
                paths = [agent_dir.evidence_path(target.name)]
                if backup_name is not None:
                    paths.insert(0, agent_dir.evidence_path(backup_name))
                raise CodexAgentNoClobberConflict("target changed before backup cleanup", paths)
            if backup_name is not None:
                if moved_state is None:
                    raise OSError("moved backup state disappeared")
                try:
                    backup_cleanup = agent_dir.cleanup_owned_entry(backup_name, moved_state)
                except OSError as cleanup_exc:
                    backup_path_text = agent_dir.evidence_path(backup_name)
                    target_path_text = agent_dir.evidence_path(target.name)
                    cleanup_errors = [
                        agent_dir.preserved_concurrent_file(
                            backup_path_text,
                            "secondary_backup_cleanup_failure",
                        )
                    ]
                    backup_name = None
                    raise CodexAgentNoClobberConflict(
                        str(cleanup_exc),
                        [backup_path_text, target_path_text],
                        cleanup_errors,
                    ) from cleanup_exc
                agent_dir.record_cleanup_result(backup_cleanup)
                if backup_cleanup.public_conflicts or (
                    isinstance(agent_dir, WindowsAnchoredAgentDir) and backup_cleanup.cleanup_errors
                ):
                    backup_name = None
                    raise CodexAgentNoClobberConflict(
                        "prior-state backup cleanup failed",
                        list(dict.fromkeys([*backup_cleanup.preserved_paths, agent_dir.evidence_path(target.name)])),
                        backup_cleanup.cleanup_errors,
                    ) from None
                backup_name = None
            if not agent_dir.state_matches(target.name, prepared_state):
                paths = [agent_dir.evidence_path(target.name)]
                state_to_preserve = cleanup_race_state if cleanup_race_state is not None else moved_state
                if state_to_preserve is not None:
                    paths.insert(0, agent_dir.preserve_state_as_backup(state_to_preserve, target.name))
                raise CodexAgentNoClobberConflict("target changed during backup cleanup", paths)
            return installed_state
        except OSError as exc:
            preserved_paths = list(exc.preserved_paths) if isinstance(exc, CodexAgentNoClobberConflict) else []
            preserved_cleanup_errors = list(exc.cleanup_errors) if isinstance(exc, CodexAgentNoClobberConflict) else []
            if tmp_name is not None:
                if prepared_state is not None:
                    agent_dir.cleanup_entry_for_packaging(
                        tmp_name,
                        prepared_state,
                        preserved_paths,
                        preserved_cleanup_errors,
                        "secondary_temp_cleanup_failure",
                    )
                else:
                    temp_cleanup = agent_dir.preserve_uncertain_entry(tmp_name, "temp_state_capture_unavailable")
                    preserved_cleanup_errors.extend(temp_cleanup.cleanup_errors)
                    if temp_cleanup.preserved_paths:
                        preserved_paths.extend(temp_cleanup.preserved_paths)
                    else:
                        tmp_path_text = agent_dir.evidence_path(tmp_name)
                        preserved_paths = [path for path in preserved_paths if path != tmp_path_text]
            if backup_name is not None:
                backup_path_text = agent_dir.evidence_path(backup_name)
                target_path_text = agent_dir.evidence_path(target.name)
                if isinstance(exc, CodexAgentNoClobberConflict):
                    preserved_paths.append(backup_path_text)
                    if agent_dir.previous_state_exists_for_packaging(
                        target.name,
                        preserved_paths,
                        preserved_cleanup_errors,
                        "secondary_target_read_failure",
                    ):
                        preserved_paths.append(target_path_text)
                elif not agent_dir.previous_state_exists_for_packaging(
                    target.name,
                    preserved_paths,
                    preserved_cleanup_errors,
                    "secondary_target_read_failure",
                ):
                    try:
                        agent_dir.restore_backup_no_clobber(backup_name, target.name)
                        backup_name = None
                    except CodexAgentNoClobberConflict as restore_exc:
                        preserved_paths.extend(restore_exc.preserved_paths)
                        preserved_cleanup_errors.extend(restore_exc.cleanup_errors)
                    except OSError as restore_exc:
                        agent_dir.restore_failure_for_packaging(
                            restore_exc,
                            backup_name,
                            target.name,
                            preserved_paths,
                            preserved_cleanup_errors,
                            "secondary_restore_failure",
                        )
                        backup_name = None
                else:
                    preserved_paths.extend([backup_path_text, target_path_text])
            if preserved_paths:
                raise CodexAgentNoClobberConflict(
                    str(exc),
                    list(dict.fromkeys(preserved_paths)),
                    preserved_cleanup_errors,
                ) from exc
            raise


def remove_codex_agent_if_unchanged(
    target: Path,
    expected_state: CodexAgentFileState | None,
    destination: Path,
    destination_identity: tuple[int, int] | None,
) -> None:
    if expected_state is None:
        raise OSError("removal requires a captured file state")
    if destination_identity is None:
        destination_identity = codex_agent_destination_identity(destination)
    with codex_agent_borrow_anchored_directory(destination, destination_identity) as agent_dir:
        if target.parent != destination or not agent_dir.target_is_safe(target.name):
            raise OSError("unsafe removal target")
        backup_name = agent_dir.move_target_to_backup(target.name, expected_state)
        moved_state: CodexAgentFileState | None = None
        try:
            moved_state = agent_dir.previous_state(backup_name)
            if moved_state != expected_state:
                try:
                    agent_dir.restore_backup_no_clobber(backup_name, target.name)
                except OSError as restore_exc:
                    preserved_paths: list[str] = []
                    cleanup_errors: list[dict[str, str]] = []
                    agent_dir.restore_failure_for_packaging(
                        restore_exc,
                        backup_name,
                        target.name,
                        preserved_paths,
                        cleanup_errors,
                        "secondary_restore_failure",
                    )
                    backup_name = None
                    raise CodexAgentNoClobberConflict(
                        "removal target changed before no-clobber removal",
                        list(dict.fromkeys(preserved_paths)),
                        cleanup_errors,
                    ) from restore_exc
                backup_name = None
                raise OSError("removal target changed before no-clobber removal")
            if agent_dir.previous_state(target.name) is not None:
                raise CodexAgentNoClobberConflict(
                    "target appeared during no-clobber removal",
                    [agent_dir.evidence_path(backup_name), agent_dir.evidence_path(target.name)],
                )
            try:
                backup_cleanup = agent_dir.cleanup_owned_entry(backup_name, expected_state)
            except OSError as cleanup_exc:
                backup_path_text = agent_dir.evidence_path(backup_name)
                cleanup_errors = [
                    agent_dir.preserved_concurrent_file(
                        backup_path_text,
                        "secondary_backup_cleanup_failure",
                    )
                ]
                backup_name = None
                raise CodexAgentNoClobberConflict(
                    str(cleanup_exc),
                    [backup_path_text],
                    cleanup_errors,
                ) from cleanup_exc
            agent_dir.record_cleanup_result(backup_cleanup)
            if backup_cleanup.public_conflicts or (
                isinstance(agent_dir, WindowsAnchoredAgentDir) and backup_cleanup.cleanup_errors
            ):
                backup_name = None
                raise CodexAgentNoClobberConflict(
                    "prior-state backup cleanup failed during removal",
                    backup_cleanup.preserved_paths,
                    backup_cleanup.cleanup_errors,
                ) from None
            backup_name = None
            if not agent_dir.state_matches(target.name, None):
                if moved_state is None:
                    raise OSError("moved removal state disappeared")
                preserved = agent_dir.preserve_state_as_backup(moved_state, target.name)
                raise CodexAgentNoClobberConflict(
                    "target appeared before no-clobber removal completed",
                    [preserved, agent_dir.evidence_path(target.name)],
                )
        except OSError as exc:
            preserved_paths = list(exc.preserved_paths) if isinstance(exc, CodexAgentNoClobberConflict) else []
            preserved_cleanup_errors = list(exc.cleanup_errors) if isinstance(exc, CodexAgentNoClobberConflict) else []
            if backup_name is not None:
                backup_path_text = agent_dir.evidence_path(backup_name)
                target_path_text = agent_dir.evidence_path(target.name)
                if isinstance(exc, CodexAgentNoClobberConflict):
                    preserved_paths.append(backup_path_text)
                    if agent_dir.previous_state_exists_for_packaging(
                        target.name,
                        preserved_paths,
                        preserved_cleanup_errors,
                        "secondary_target_read_failure",
                    ):
                        preserved_paths.append(target_path_text)
                elif not agent_dir.previous_state_exists_for_packaging(
                    target.name,
                    preserved_paths,
                    preserved_cleanup_errors,
                    "secondary_target_read_failure",
                ):
                    try:
                        agent_dir.restore_backup_no_clobber(backup_name, target.name)
                        backup_name = None
                    except CodexAgentNoClobberConflict as restore_exc:
                        preserved_paths.extend(restore_exc.preserved_paths)
                        preserved_cleanup_errors.extend(restore_exc.cleanup_errors)
                    except OSError as restore_exc:
                        agent_dir.restore_failure_for_packaging(
                            restore_exc,
                            backup_name,
                            target.name,
                            preserved_paths,
                            preserved_cleanup_errors,
                            "secondary_restore_failure",
                        )
                        backup_name = None
                else:
                    preserved_paths.extend([backup_path_text, target_path_text])
            if preserved_paths:
                raise CodexAgentNoClobberConflict(
                    str(exc),
                    list(dict.fromkeys(preserved_paths)),
                    preserved_cleanup_errors,
                ) from exc
            raise


def codex_agent_open_anchored_directory(
    destination: Path,
    destination_identity: tuple[int, int] | None,
) -> int:
    if os.name == "nt":
        raise OSError(errno.ENOTSUP, "Windows anchored directory backend is unavailable")
    if not CODEX_AGENT_OPEN_SUPPORTS_DIR_FD:
        raise OSError(errno.ENOTSUP, "descriptor-relative anchored directory operations are unavailable")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(destination, flags)
    metadata = os.fstat(descriptor)
    if destination_identity is None or (metadata.st_dev, metadata.st_ino) != destination_identity:
        codex_agent_close_descriptor_nonmasking(descriptor)
        raise OSError("destination changed before anchored operation")
    return descriptor


def codex_agent_native_rename_no_replace_between(
    source_directory_fd: int,
    source_name: str,
    target_directory_fd: int,
    target_name: str,
) -> None:
    library = ctypes.CDLL(None, use_errno=True)
    source = os.fsencode(source_name)
    target = os.fsencode(target_name)
    if sys.platform == "darwin":
        try:
            function = library.renameatx_np
        except AttributeError as exc:
            raise OSError(errno.ENOTSUP, "renameatx_np is unavailable") from exc
        function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        result = function(source_directory_fd, source, target_directory_fd, target, 0x00000004)
    elif sys.platform.startswith("linux"):
        try:
            function = library.renameat2
        except AttributeError as exc:
            raise OSError(errno.ENOTSUP, "renameat2 is unavailable") from exc
        function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        result = function(source_directory_fd, source, target_directory_fd, target, 0x00000001)
    else:
        raise OSError(errno.ENOTSUP, "anchored atomic no-replace rename is unavailable")
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), target_name)


def codex_agent_native_rename_no_replace(directory_fd: int, source_name: str, target_name: str) -> None:
    codex_agent_native_rename_no_replace_between(directory_fd, source_name, directory_fd, target_name)


def codex_agent_rename_path_no_replace(source: Path, target: Path) -> None:
    if source.parent != target.parent:
        raise OSError(errno.EXDEV, "anchored no-replace directory quarantine requires one parent")
    if os.name == "nt":
        raise OSError(errno.ENOTSUP, "Windows identity-bound directory quarantine requires a handle backend")
    parent_fd: int | None = None
    try:
        parent_fd = os.open(
            source.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        codex_agent_native_rename_no_replace(parent_fd, source.name, target.name)
    finally:
        if parent_fd is not None:
            codex_agent_close_descriptor_nonmasking(parent_fd)


def codex_agent_move_target_to_backup(
    target: Path,
    destination: Path,
    destination_identity: tuple[int, int] | None = None,
) -> Path:
    if destination_identity is None:
        destination_identity = codex_agent_destination_identity(destination)
    with codex_agent_borrow_anchored_directory(destination, destination_identity) as agent_dir:
        moved_name = agent_dir.move_target_to_backup(target.name)
        return destination / moved_name


def codex_agent_previous_state_at(directory_fd: int, name: str) -> CodexAgentFileState | None:
    try:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise OSError("managed target is not a regular file")
    descriptor = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=directory_fd,
    )
    try:
        opened_metadata = os.fstat(descriptor)
        if (opened_metadata.st_dev, opened_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise OSError("managed target changed while being read")
        content_parts: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            content_parts.append(chunk)
        final_metadata = os.fstat(descriptor)
        if (final_metadata.st_dev, final_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise OSError("managed target changed while being read")
        return CodexAgentFileState(
            content=b"".join(content_parts),
            mode=final_metadata.st_mode,
            device=final_metadata.st_dev,
            inode=final_metadata.st_ino,
        )
    finally:
        codex_agent_close_descriptor_nonmasking(descriptor)


def codex_agent_restore_backup_no_clobber(
    backup: Path,
    target: Path,
    destination: Path | None = None,
    destination_identity: tuple[int, int] | None = None,
) -> None:
    if destination is None:
        destination = target.parent
    if destination_identity is None:
        destination_identity = codex_agent_destination_identity(destination)
    with codex_agent_borrow_anchored_directory(destination, destination_identity) as agent_dir:
        agent_dir.restore_backup_no_clobber(backup.name, target.name)


def codex_agent_preserve_state_as_backup(
    state: CodexAgentFileState,
    target: Path,
    destination: Path,
    destination_identity: tuple[int, int] | None,
) -> Path:
    if destination_identity is None:
        destination_identity = codex_agent_destination_identity(destination)
    try:
        with codex_agent_borrow_anchored_directory(destination, destination_identity) as agent_dir:
            result = agent_dir.preserve_state_as_backup(state, target.name)
    except CodexAgentRecoveryCopyFailure:
        raise
    except OSError as exc:
        raise CodexAgentRecoveryCopyFailure(
            "could not create a verified anchored recovery copy",
            [],
            [],
        ) from exc
    return Path(result)


def codex_agent_target_is_safe(
    target: Path,
    destination: Path,
    destination_identity: tuple[int, int] | None,
) -> bool:
    active = codex_agent_current_anchored_directory(destination, destination_identity)
    if active is not None and target.parent == destination:
        return active.target_is_safe(target.name)
    try:
        current_identity = codex_agent_destination_identity(destination)
    except OSError:
        return False
    if destination_identity is None or current_identity != destination_identity or target.parent != destination:
        return False
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode)


def verify_codex_agent_install(destination: Path, rendered: dict[str, bytes]) -> list[str]:
    mismatches: list[str] = []
    for name, content in rendered.items():
        target = destination / name
        try:
            state = codex_agent_previous_state(target)
            if state is None or state.content != content:
                mismatches.append(name)
        except OSError:
            mismatches.append(name)
    return sorted(mismatches)


def codex_agent_install_data(
    entry: Any,
    request: Any,
    mutation: dict[str, Any],
    source_dir: Path,
    destination: Path,
    model: str,
    rendered: dict[str, bytes],
) -> dict[str, Any]:
    return {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": False,
        "source": source_dir.as_posix(),
        "destination": destination.as_posix(),
        "model": model,
        "agent_files": sorted(rendered),
        "restart_required": request.mode == "apply",
        "verification": {"status": "planned", "matched_files": []},
        "mutation": mutation,
    }


