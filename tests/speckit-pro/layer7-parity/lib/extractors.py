#!/usr/bin/env python3
"""Layer 7 section/table extractors for parity comparison."""

from __future__ import annotations

from pathlib import Path


class ExtractorError(Exception):
    """Raised when a section table or column cannot be located."""


def _read_lines(file: str | Path) -> list[str]:
    return Path(file).read_text(encoding="utf-8").splitlines()


def extract_section(file: str | Path, header: str) -> str:
    """Return the body of the named H2 section, excluding the H2 line itself."""
    target = f"## {header}"
    inside = False
    output: list[str] = []
    for line in _read_lines(file):
        if line == target:
            inside = True
            continue
        if inside and line.startswith("## "):
            inside = False
        if inside:
            output.append(line)
    return "\n".join(output)


def _first_table(section: str) -> list[str]:
    table: list[str] = []
    in_table = False
    for line in section.splitlines():
        if line.startswith("|"):
            in_table = True
            table.append(line)
            continue
        if in_table:
            break
    return table


def _section_table(file: str | Path, header: str) -> list[str]:
    table = _first_table(extract_section(file, header))
    if not table:
        raise ExtractorError("section table not found")
    return table


def extract_table_row_count(file: str | Path, header: str) -> str:
    """Return the first table's data-row count as stdout-compatible text."""
    table = _section_table(file, header)
    total = sum(1 for line in table if line.startswith("|"))
    if total < 2:
        return "0"
    return str(total - 2)


def _trimmed_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.split("|")]


def extract_table_column(file: str | Path, header: str, column: str) -> str:
    """Return one value per data row from ``column``, newline-separated."""
    table = _section_table(file, header)
    header_cells = _trimmed_cells(table[0])
    column_index = None
    for index in range(1, len(header_cells) - 1):
        if header_cells[index] == column:
            column_index = index
            break
    if column_index is None:
        raise ExtractorError("table column not found")

    values: list[str] = []
    for line in table[2:]:
        cells = _trimmed_cells(line)
        if len(cells) >= column_index + 2:
            values.append(cells[column_index])
    return "\n".join(values)


__all__ = (
    "ExtractorError",
    "extract_section",
    "extract_table_column",
    "extract_table_row_count",
)
