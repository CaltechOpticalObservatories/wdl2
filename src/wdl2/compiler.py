# -----------------------------------------------------------------------------
# @file     compiler.py
# @brief    parse a source file into a typed AST
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2,
#     a rewrite of WDL1 as a self-contained Python compiler. Distributed
#     under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Public front end for the wdl2 compiler.

Loads the packaged lark grammars, builds and caches the parsers, and exposes
the parse_* functions that turn a source file into a typed AST. No semantic
checking or code generation happens here, only parsing. For now only the
native WDL 2.0 grammar is wired up. Legacy (WDL1) parsing and the legacy
preprocessor are added in later steps.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from lark import Lark

from .ast.nodes import Node
from .ast.transform import NativeTransformer


# -----------------------------------------------------------------------------
# @fn       _grammar_source
# @brief    read a packaged .lark grammar file as text
# @details  Grammars ship inside the wdl2.grammar package, so they are read
#           through importlib.resources rather than a filesystem path. This
#           works whether the package is installed or run from a wheel.
# @param    name   grammar file name within the wdl2.grammar package
# @return   the grammar source as a string
# -----------------------------------------------------------------------------
def _grammar_source(name: str) -> str:
    return resources.files("wdl2.grammar").joinpath(name).read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# @fn       _make_lark
# @brief    build a LALR lark parser from a packaged grammar file
# @details  Position propagation is enabled so every rule carries the line and
#           column span the transformer turns into a SrcLoc. Placeholders keep
#           optional children present (as None) so child indices stay stable.
# @param    grammar_file   grammar file name
# @param    start          start rule, or list of start rules
# @return   a configured Lark parser
# -----------------------------------------------------------------------------
def _make_lark(grammar_file: str, start: str | list[str]) -> Lark:
    return Lark(
        _grammar_source(grammar_file),
        parser="lalr",
        start=start,
        propagate_positions=True,
        maybe_placeholders=True,
    )


# The parser is comparatively expensive to build, so build it once on first use.
_native_parser: Lark | None = None


# -----------------------------------------------------------------------------
# @fn       native_parser
# @brief    return the shared native-grammar parser, building it on first use
# @details  The parser is comparatively expensive to construct, so it is built
#           once and cached in a module-global. Later calls return that instance.
# @return   the native Lark parser
# -----------------------------------------------------------------------------
def native_parser() -> Lark:
    global _native_parser
    if _native_parser is None:
        _native_parser = _make_lark("wdl2.lark", start="start")
    return _native_parser


# -----------------------------------------------------------------------------
# @fn       parse_native
# @brief    parse a native .wdl2 source file into a typed AST
# @details  Reads the file, parses it through the native grammar, then runs the
#           native transformer to produce the typed tree. The file path is
#           carried into every node's SrcLoc for later diagnostics.
# @param    path   path to the .wdl2 source file
# @return   the Program node at the root of the AST
# -----------------------------------------------------------------------------
def parse_native(path: str | Path) -> Node:
    p = Path(path)
    tree = native_parser().parse(p.read_text(encoding="utf-8"))
    return NativeTransformer(str(p)).transform(tree)
