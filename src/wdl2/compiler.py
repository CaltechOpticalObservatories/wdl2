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
checking or code generation happens here, only parsing. Both the native
WDL 2.0 grammar and the WDL1 (legacy) grammar are wired up.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Literal

from lark import Lark

from .ast.nodes import Node
from .ast.transform import LegacyTransformer, NativeTransformer

LegacyKind = Literal["waveform", "seq", "mod"]


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


# The parsers are comparatively expensive to build, so build each once on first use.
_native_parser: Lark | None = None
_legacy_parser: Lark | None = None


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
# @fn      legacy_parser
# @brief   return the shared legacy (WDL1) parser, building it on first use
# @details The legacy grammar has a start rule per WDL1 file kind (waveform /
#          seq / mod); parse_legacy selects the right one. .signals and .def are
#          preprocessor input, not parsed here.
# @return  the legacy Lark parser
# -----------------------------------------------------------------------------
def legacy_parser() -> Lark:
    global _legacy_parser
    if _legacy_parser is None:
        _legacy_parser = _make_lark(
            "legacy.lark",
            start=["waveform_file", "seq_file", "mod_file"],
        )
    return _legacy_parser


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


# -----------------------------------------------------------------------------
# @fn      parse_legacy
# @brief   parse a single post-GPP WDL1 file into a typed AST
# @details Parses through the legacy grammar using the start rule for `kind`
#          (one of waveform/seq/mod), then runs the legacy transformer.
#          This expects already-preprocessed input.
# @param   path   path to the legacy source file
# @param   kind   which WDL1 file kind this is
# @return  the root node of the AST
# -----------------------------------------------------------------------------
def parse_legacy(path: str | Path, kind: LegacyKind) -> Node:
    p = Path(path)
    tree = legacy_parser().parse(p.read_text(encoding="utf-8"), start=f"{kind}_file")
    return LegacyTransformer(str(p)).transform(tree)
