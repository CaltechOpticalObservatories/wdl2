# -----------------------------------------------------------------------------
# @file     nodes.py
# @brief    typed AST nodes for WDL 2.0
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

"""Typed AST nodes for WDL 2.0.

One frozen dataclass per construct. Every node carries a SrcLoc. Both the
native and the legacy transformer build their trees from this one shared set
of nodes, so the constructs are introduced here as the language grows. Nodes
are frozen (immutable, hashable, safe to share across passes) and use slots
(lower memory, attribute-typo protection).
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Literal

from .source import SrcLoc


# -----------------------------------------------------------------------------
# node base
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Node:
    """Base class for every AST node. The source location is keyword-only so
    that subclasses are free to declare positional fields of their own."""

    loc: SrcLoc = field(kw_only=True)


# -----------------------------------------------------------------------------
# expressions
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class IntLit(Node):
    value: int


@dataclass(frozen=True, slots=True)
class FloatLit(Node):
    value: float


@dataclass(frozen=True, slots=True)
class IdentRef(Node):
    name: str


@dataclass(frozen=True, slots=True)
class BinOp(Node):
    op: Literal["+", "-", "*", "/", "%"]
    lhs: "Expr"
    rhs: "Expr"


@dataclass(frozen=True, slots=True)
class UnaryOp(Node):
    op: Literal["-"]
    operand: "Expr"


Expr = IntLit | FloatLit | IdentRef | BinOp | UnaryOp


# -----------------------------------------------------------------------------
# signal values (slot:chan typed literals and group aliases)
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SlotChan(Node):
    slot: int
    chan: int


@dataclass(frozen=True, slots=True)
class SignalRef(Node):
    name: str


@dataclass(frozen=True, slots=True)
class SignalGroup(Node):
    members: tuple["SignalValue", ...]


SignalValue = SlotChan | SignalRef | SignalGroup


# -----------------------------------------------------------------------------
# top-level declarations
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Include(Node):
    path: str


@dataclass(frozen=True, slots=True)
class ConstDecl(Node):
    name: str
    value: Expr


@dataclass(frozen=True, slots=True)
class ParamDecl(Node):
    name: str
    value: Expr


@dataclass(frozen=True, slots=True)
class SignalItem(Node):
    name: str
    value: SignalValue


@dataclass(frozen=True, slots=True)
class SignalsBlock(Node):
    items: tuple[SignalItem, ...]


@dataclass(frozen=True, slots=True)
class SignalsNoop(Node):
    """Legacy WDL1 `SIGNALS { }` no-op block. Accepted in --legacy only."""


# -----------------------------------------------------------------------------
# slot block (generic SLOT directives)
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SlotDir(Node):
    keyword: str
    chan: int | None
    args: tuple[Expr, ...]
    label: str | None


@dataclass(frozen=True, slots=True)
class SlotBlock(Node):
    num: int
    kind: str
    directives: tuple[SlotDir, ...]


# -----------------------------------------------------------------------------
# waveform
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class PythonExt(Node):
    """Legacy WAVEFORM name.attr(args) metaprogramming hook. Populated only by
    the legacy transformer. Native waveforms never carry one."""

    attr: str
    args: tuple[Expr, ...]


@dataclass(frozen=True, slots=True)
class Slew(Node):
    kind: Literal["FAST", "SLOW"]


# A SET target is a signal reference or a slot:chan literal. Group targets are
# expressed by a tuple in SetStmt.target_group instead.
SetTarget = SignalRef | SlotChan


@dataclass(frozen=True, slots=True)
class SetStmt(Node):
    # Exactly one of target or target_group is non-None.
    target: SetTarget | None
    target_group: tuple[SetTarget, ...] | None
    value: Expr
    slew: Slew | None


@dataclass(frozen=True, slots=True)
class TimeAbsolute(Node):
    expr: Expr


@dataclass(frozen=True, slots=True)
class TimeRelative(Node):
    """`.+expr`. Adds to the previous evaluated time."""

    expr: Expr


TimeDesignator = TimeAbsolute | TimeRelative


@dataclass(frozen=True, slots=True)
class ReturnStmt(Node):
    alt_name: str | None  # legacy `RETURN AltName;`. None in native


@dataclass(frozen=True, slots=True)
class WfTimedStmt(Node):
    time: TimeDesignator
    label: str | None
    sets: tuple[SetStmt, ...]
    ret: ReturnStmt | None  # a legacy timed line may carry a RETURN as its body


@dataclass(frozen=True, slots=True)
class WfBareSet(Node):
    """A SET line with no time prefix. Inherits the previous time."""

    set: SetStmt


WfStmt = WfTimedStmt | WfBareSet | ReturnStmt


@dataclass(frozen=True, slots=True)
class WaveformBlock(Node):
    name: str
    pyext: PythonExt | None
    stmts: tuple[WfStmt, ...]


# -----------------------------------------------------------------------------
# sequence
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class CallStmt(Node):
    target: str
    arg: Expr | None
    explicit: bool  # True if the CALL keyword was present


@dataclass(frozen=True, slots=True)
class GotoStmt(Node):
    target: str


@dataclass(frozen=True, slots=True)
class IfStmt(Node):
    negated: bool
    param: str
    body: "SeqStmt"


@dataclass(frozen=True, slots=True)
class IncDec(Node):
    name: str
    op: Literal["++", "--"]


SeqStmt = CallStmt | GotoStmt | IfStmt | ReturnStmt | IncDec


@dataclass(frozen=True, slots=True)
class SequenceBlock(Node):
    name: str
    stmts: tuple[SeqStmt, ...]


# -----------------------------------------------------------------------------
# modes
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ModeEntry(Node):
    section: str | None
    key: str
    value: str


@dataclass(frozen=True, slots=True)
class ModeBlock(Node):
    name: str
    entries: tuple[ModeEntry, ...]


# -----------------------------------------------------------------------------
# top-level program container
# -----------------------------------------------------------------------------
# TopItem gains the block forms (signals, slot, waveform, sequence, mode) as
# those constructs are added in later steps. Program is the AST root.

TopItem = (
    Include
    | ConstDecl
    | ParamDecl
    | SignalsBlock
    | SignalsNoop
    | SlotBlock
    | WaveformBlock
    | SequenceBlock
    | ModeBlock
)


@dataclass(frozen=True, slots=True)
class Program(Node):
    items: tuple[TopItem, ...]


# -----------------------------------------------------------------------------
# visitor base
# -----------------------------------------------------------------------------

class Visitor:
    """Generic tree walker. Dispatch is on a node's concrete class name:
    override visit_<ClassName> for the nodes of interest, and anything else
    falls through to generic_visit, which recurses over the dataclass fields.
    """

    # -------------------------------------------------------------------------
    # @fn       visit
    # @brief    dispatch to visit_<ClassName>, or generic_visit when absent
    # @details  Looks up a method named for the node's concrete class. This is
    #           how a subclass handles only the node kinds it cares about.
    # @param    node   the AST node to visit
    # @return   whatever the dispatched method returns
    # -------------------------------------------------------------------------
    def visit(self, node: Node):
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is None:
            return self.generic_visit(node)
        return method(node)

    # -------------------------------------------------------------------------
    # @fn       generic_visit
    # @brief    default visit. recurse over every field except the source loc
    # @details  Discovers children by reflection over the dataclass fields, so
    #           new node types need no change here. The loc field is skipped.
    # @param    node   the AST node whose children are visited
    # @return   None
    # -------------------------------------------------------------------------
    def generic_visit(self, node: Node):
        for f in fields(node):
            if f.name == "loc":
                continue
            value = getattr(node, f.name)
            self._visit_value(value)

    # -------------------------------------------------------------------------
    # @fn       _visit_value
    # @brief    visit one field value, descending into nodes and tuples of nodes
    # @details  Children are stored as tuples (to stay immutable), so a tuple is
    #           walked element by element. Non-node values are simply ignored.
    # @param    value   a field value pulled from a node
    # @return   None
    # -------------------------------------------------------------------------
    def _visit_value(self, value) -> None:
        if isinstance(value, Node):
            self.visit(value)
        elif isinstance(value, tuple):
            for item in value:
                self._visit_value(item)
