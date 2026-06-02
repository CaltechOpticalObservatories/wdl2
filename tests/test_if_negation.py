# -----------------------------------------------------------------------------
# @file     test_if_negation.py
# @brief    IF !param negation is supported (WDL1 issue #30)
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2.
#     Distributed under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""`IF !param body` is supported in native source (WDL1 issue #30).

WDL1 only honored `!` for param, not const. DECISIONS.md mandates parity. The
matching legacy-grammar check is added once the legacy grammar exists.
"""

from __future__ import annotations

from wdl2.ast.nodes import CallStmt, IfStmt, Program, SequenceBlock
from wdl2.ast.transform import NativeTransformer
from wdl2.compiler import native_parser


# -----------------------------------------------------------------------------
# @fn      _extract_if
# @brief   return the first IF statement found in a program's sequences
# @details Walks the program's top-level items for a sequence block, then that
#          block's statements for an IfStmt. Raises if none is found, so a
#          missing IF fails the test loudly.
# @param   prog   the parsed Program node
# @return  the first IfStmt node
# -----------------------------------------------------------------------------
def _extract_if(prog: Program) -> IfStmt:
    for item in prog.items:
        if isinstance(item, SequenceBlock):
            for stmt in item.stmts:
                if isinstance(stmt, IfStmt):
                    return stmt
    raise AssertionError("no IF statement found in program")


def test_native_if_negation() -> None:
    text = """
    sequence Foo {
      if !Abort Cleanup();
      return;
    }
    """
    tree = native_parser().parse(text)
    prog = NativeTransformer("<test>").transform(tree)
    stmt = _extract_if(prog)
    assert stmt.negated is True
    assert stmt.param == "Abort"
    assert isinstance(stmt.body, CallStmt)
    assert stmt.body.target == "Cleanup"
