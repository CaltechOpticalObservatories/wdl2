# -----------------------------------------------------------------------------
# @file     test_native_sample.py
# @brief    parse the native sample and check every construct's node type
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2.
#     Distributed under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Parse the hand-written native sample and assert that every covered construct
produced its expected node type.
"""

from __future__ import annotations

from wdl2.ast.nodes import (
    BinOp,
    CallStmt,
    ConstDecl,
    FloatLit,
    GotoStmt,
    IdentRef,
    IfStmt,
    IncDec,
    Include,
    IntLit,
    ModeBlock,
    ModeEntry,
    ParamDecl,
    Program,
    ReturnStmt,
    SequenceBlock,
    SetStmt,
    SignalGroup,
    SignalItem,
    SignalRef,
    SignalsBlock,
    Slew,
    SlotBlock,
    SlotChan,
    TimeAbsolute,
    TimeRelative,
    WaveformBlock,
)
from wdl2.compiler import parse_native


def test_native_sample(native_sample_path) -> None:
    prog = parse_native(native_sample_path)
    assert isinstance(prog, Program)
    items = prog.items
    assert items, "sample should produce items"

    by_type: dict[type, list] = {}
    for it in items:
        by_type.setdefault(type(it), []).append(it)

    # Top-level shape
    assert Include in by_type
    assert ConstDecl in by_type
    assert ParamDecl in by_type
    assert SignalsBlock in by_type
    assert SlotBlock in by_type
    assert WaveformBlock in by_type
    assert SequenceBlock in by_type
    assert ModeBlock in by_type

    # Include carries the literal path.
    assert by_type[Include][0].path == "common.wdl2"

    # Float const works (issue #33).
    vrg = next(c for c in by_type[ConstDecl] if c.name == "VRG_HI")
    assert isinstance(vrg.value, FloatLit) and vrg.value.value == 12.5

    # Negative int const via UnaryOp.
    serial_lo = next(c for c in by_type[ConstDecl] if c.name == "SerialLo")
    # `-5` lowers to UnaryOp('-', IntLit(5))
    assert hasattr(serial_lo.value, "op") and serial_lo.value.op == "-"

    # Arithmetic expression in const.
    us = next(c for c in by_type[ConstDecl] if c.name == "us")
    assert isinstance(us.value, BinOp) and us.value.op == "/"

    # signals { } shape
    signals_block: SignalsBlock = by_type[SignalsBlock][0]
    by_name = {s.name: s for s in signals_block.items}
    assert isinstance(by_name["RG"].value, SlotChan)
    assert by_name["RG"].value.slot == 12 and by_name["RG"].value.chan == 1
    pclock = by_name["PClock"].value
    assert isinstance(pclock, SignalGroup)
    assert all(isinstance(m, SignalRef) for m in pclock.members)
    assert tuple(m.name for m in pclock.members) == ("P1", "P2", "P3")

    # SLOT block (generic, table-driven)
    slot = by_type[SlotBlock][0]
    assert slot.num == 10 and slot.kind == "lvxbias"
    keywords = [d.keyword for d in slot.directives]
    assert "LVLC" in keywords and "DIOPOWER" in keywords
    diopower = next(d for d in slot.directives if d.keyword == "DIOPOWER")
    assert diopower.chan is None and diopower.label is None

    # waveform InitClocks. time forms, group SET, slew, time label.
    wf = next(w for w in by_type[WaveformBlock] if w.name == "InitClocks")
    timed_stmts = [s for s in wf.stmts if type(s).__name__ == "WfTimedStmt"]
    bare_stmts = [s for s in wf.stmts if type(s).__name__ == "WfBareSet"]
    assert any(isinstance(t.time, TimeAbsolute) for t in timed_stmts)
    assert any(isinstance(t.time, TimeRelative) for t in timed_stmts)
    assert any(t.label == "edge" for t in timed_stmts)
    assert bare_stmts, "expected at least one bare SET inheriting previous time"

    # A SET with a group target
    group_sets = [
        t for t in timed_stmts
        if t.sets and t.sets[0].target_group is not None
    ]
    assert group_sets, "expected a SET with bracketed target group"
    g = group_sets[0].sets[0]
    assert g.slew is not None and g.slew.kind == "SLOW"
    assert len(g.target_group) == 3
    assert all(isinstance(m, SignalRef) for m in g.target_group)

    # A SET with FAST slew
    fast_sets = [
        t for t in timed_stmts
        if t.sets and isinstance(t.sets[0].slew, Slew) and t.sets[0].slew.kind == "FAST"
    ]
    assert fast_sets

    # Sequence: implicit/explicit calls, IF/IF!, GOTO, ++/--, RETURN.
    init_seq = next(s for s in by_type[SequenceBlock] if s.name == "Init")
    stmts = init_seq.stmts
    impl_calls = [s for s in stmts if isinstance(s, CallStmt) and not s.explicit]
    expl_calls = [s for s in stmts if isinstance(s, CallStmt) and s.explicit]
    assert impl_calls and expl_calls
    assert any(isinstance(s, IfStmt) and not s.negated for s in stmts)
    assert any(isinstance(s, IfStmt) and s.negated for s in stmts)
    assert any(isinstance(s, GotoStmt) for s in stmts)
    assert any(isinstance(s, IncDec) and s.op == "++" for s in stmts)
    assert any(isinstance(s, IncDec) and s.op == "--" for s in stmts)
    assert any(isinstance(s, ReturnStmt) for s in stmts)

    # Mode block
    mode = by_type[ModeBlock][0]
    assert mode.name == "DEFAULT"
    sections = {(e.section, e.key) for e in mode.entries if isinstance(e, ModeEntry)}
    assert ("ARCH", "HORI_AMPS") in sections
    assert ("ACF", "LINECOUNT") in sections
    # Source location is propagated.
    assert prog.loc.line == 1 or prog.loc.line > 0
