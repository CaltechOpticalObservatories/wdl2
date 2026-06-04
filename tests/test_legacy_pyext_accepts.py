# -----------------------------------------------------------------------------
# @file     test_legacy_pyext_accepts.py
# @brief    legacy grammar accepts the WAVEFORM Python-extension hook
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2.
#     Distributed under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Legacy grammar parses the undocumented WAVEFORM Python-extension syntax.

`WAVEFORM Foo.set_nperiods(100) { ... }` is captured as a PythonExt node on the
WaveformBlock. Native rejects it (see test_native_rejects); a deprecation
warning is a later-phase concern.
"""

from __future__ import annotations

from wdl2.ast.nodes import IntLit, Program, PythonExt, WaveformBlock
from wdl2.ast.transform import LegacyTransformer
from wdl2.compiler import legacy_parser


def test_legacy_accepts_python_extension() -> None:
    text = """
    WAVEFORM Foo.set_nperiods(100) {
      0: SET a TO 1;
    }
    """
    tree = legacy_parser().parse(text, start="waveform_file")
    prog = LegacyTransformer("<test>").transform(tree)
    assert isinstance(prog, Program)
    [wf] = prog.items
    assert isinstance(wf, WaveformBlock)
    assert wf.name == "Foo"
    assert isinstance(wf.pyext, PythonExt)
    assert wf.pyext.attr == "set_nperiods"
    assert len(wf.pyext.args) == 1
    arg = wf.pyext.args[0]
    assert isinstance(arg, IntLit) and arg.value == 100
