# -----------------------------------------------------------------------------
# @file     test_const_float.py
# @brief    const accepts float values unconditionally (WDL1 issue #33)
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2.
#     Distributed under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""`const NAME = <float>` is accepted unconditionally by both the native and
legacy grammars (resolves WDL1 issue #33, which rejected floats in const).
"""

from __future__ import annotations

from wdl2.ast.nodes import ConstDecl, FloatLit, Program
from wdl2.ast.transform import LegacyTransformer, NativeTransformer
from wdl2.compiler import legacy_parser, native_parser


# -----------------------------------------------------------------------------
# @fn       _const
# @brief    find the const declaration with the given name in a program
# @details  Walks the program's top-level items and returns the first ConstDecl
#           whose name matches and raises if none is found, so a missing const
#           fails the test loudly rather than silently.
# @param    prog   the parsed Program node
# @param    name   the const name to look for
# @return   the matching ConstDecl node
# -----------------------------------------------------------------------------
def _const(prog: Program, name: str) -> ConstDecl:
    for item in prog.items:
        if isinstance(item, ConstDecl) and item.name == name:
            return item
    raise AssertionError(f"no const named {name!r} in program")


def test_native_const_float() -> None:
    text = "const VRG_HI = 12.5;\n"
    tree = native_parser().parse(text)
    prog = NativeTransformer("<test>").transform(tree)
    c = _const(prog, "VRG_HI")
    assert isinstance(c.value, FloatLit) and c.value.value == 12.5


def test_legacy_const_float() -> None:
    # const lives at the top of a WDL1 .seq file; the semicolon is optional.
    text = "const VRG_HI = 12.5\n"
    tree = legacy_parser().parse(text, start="seq_file")
    prog = LegacyTransformer("<test>").transform(tree)
    c = _const(prog, "VRG_HI")
    assert isinstance(c.value, FloatLit) and c.value.value == 12.5
