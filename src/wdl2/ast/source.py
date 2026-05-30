# -----------------------------------------------------------------------------
# @file     source.py
# @brief    source-location record carried on every AST node
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2,
#     a rewrite of WDL1 as a self-contained Python compiler.  Distributed
#     under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Source-location record carried on every AST node."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SrcLoc:
    """Pins a node to its span in the original source text: the file, the
    1-based start line and column, and the end line and column."""

    file: str
    line: int
    col: int
    end_line: int
    end_col: int

    # -------------------------------------------------------------------------
    # @fn     unknown
    # @brief  build a placeholder location for synthesized nodes
    # @param  file   optional file name to record (defaults to "<unknown>")
    # @return SrcLoc with zeroed line and column fields
    # -------------------------------------------------------------------------
    @classmethod
    def unknown(cls, file: str = "<unknown>") -> "SrcLoc":
        return cls(file=file, line=0, col=0, end_line=0, end_col=0)
