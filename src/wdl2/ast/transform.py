# -----------------------------------------------------------------------------
# @file     transform.py
# @brief    lark transformers. parse trees become typed AST nodes
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

"""Lark transformers: parse trees become typed AST nodes.

NativeTransformer turns a wdl2.lark parse tree into the typed AST. Its
expression handling lives in a common base, _BaseTransformer, which the (later)
legacy transformer shares. The transformers build nodes and do no semantic
checking (diagnostics come later). There is one rule-method per grammar rule of
interest and lark dispatches to it by name.
"""

from __future__ import annotations

from typing import Any

from lark import Token, Transformer, v_args
from lark.tree import Meta

from .nodes import (
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
    SlotDir,
    TimeAbsolute,
    TimeRelative,
    UnaryOp,
    WaveformBlock,
    WfBareSet,
    WfTimedStmt,
)
from .source import SrcLoc


# -----------------------------------------------------------------------------
# @fn       _str
# @brief    render a lark token (or anything) as a plain string
# @details  lark hands rule children back as Token objects (a str subclass) or
#           as already-built nodes. This normalizes a token to a plain str so
#           downstream code never carries Token instances into the AST.
# @param    token   a lark Token or other value
# @return   the string form
# -----------------------------------------------------------------------------
def _str(token: Token | Any) -> str:
    return str(token)


# -----------------------------------------------------------------------------
# base transformer
# -----------------------------------------------------------------------------

class _BaseTransformer(Transformer):
    """Rule methods shared between the native and the legacy transformers."""

    def __init__(self, file: str) -> None:
        super().__init__()
        self._file = file

    # -------------------------------------------------------------------------
    # @fn       _loc
    # @brief    build a SrcLoc from a lark rule's position metadata
    # @details  Position info is present because the parser is built with
    #           propagate_positions. Rules with no span (rare, synthesized)
    #           fall back to an unknown location so a SrcLoc is always present.
    # @param    meta   lark Meta for the rule (may be empty for some rules)
    # @return   a SrcLoc spanning the rule, or an unknown loc when unavailable
    # -------------------------------------------------------------------------
    def _loc(self, meta: Meta) -> SrcLoc:
        if meta is None or meta.empty:
            return SrcLoc.unknown(self._file)
        return SrcLoc(
            file=self._file,
            line=meta.line,
            col=meta.column,
            end_line=meta.end_line,
            end_col=meta.end_column,
        )

    # -------------------------------------------------------------------------
    # expressions: one method per operator rule. Each receives the already
    # transformed operand nodes in `children`, wraps them in a BinOp/UnaryOp,
    # and tags the new node with its source location.
    # -------------------------------------------------------------------------
    @v_args(meta=True)
    def int_atom(self, meta: Meta, children: list) -> IntLit:
        return IntLit(value=int(children[0]), loc=self._loc(meta))

    @v_args(meta=True)
    def float_atom(self, meta: Meta, children: list) -> FloatLit:
        return FloatLit(value=float(children[0]), loc=self._loc(meta))

    @v_args(meta=True)
    def ident_atom(self, meta: Meta, children: list) -> IdentRef:
        return IdentRef(name=_str(children[0]), loc=self._loc(meta))

    @v_args(meta=True)
    def add(self, meta: Meta, children: list) -> BinOp:
        return BinOp(op="+", lhs=children[0], rhs=children[1], loc=self._loc(meta))

    @v_args(meta=True)
    def sub(self, meta: Meta, children: list) -> BinOp:
        return BinOp(op="-", lhs=children[0], rhs=children[1], loc=self._loc(meta))

    @v_args(meta=True)
    def mul(self, meta: Meta, children: list) -> BinOp:
        return BinOp(op="*", lhs=children[0], rhs=children[1], loc=self._loc(meta))

    @v_args(meta=True)
    def div(self, meta: Meta, children: list) -> BinOp:
        return BinOp(op="/", lhs=children[0], rhs=children[1], loc=self._loc(meta))

    @v_args(meta=True)
    def mod(self, meta: Meta, children: list) -> BinOp:
        return BinOp(op="%", lhs=children[0], rhs=children[1], loc=self._loc(meta))

    @v_args(meta=True)
    def neg(self, meta: Meta, children: list) -> UnaryOp:
        return UnaryOp(op="-", operand=children[0], loc=self._loc(meta))

    def pos(self, children: list):
        # unary `+` is a no-op (the samples use `+25us:` as a time prefix)
        return children[0]

    def arg_list(self, children: list) -> tuple:
        return tuple(children)

    def arg(self, children: list) -> Any:
        return children[0]

    # -------------------------------------------------------------------------
    # slot:chan literal. Shared by signals, set targets, and signal defines
    # -------------------------------------------------------------------------
    @v_args(meta=True)
    def slot_chan(self, meta: Meta, children: list) -> SlotChan:
        return SlotChan(slot=int(children[0]), chan=int(children[1]), loc=self._loc(meta))


# -----------------------------------------------------------------------------
# native transformer
# -----------------------------------------------------------------------------

class NativeTransformer(_BaseTransformer):
    """Builds the typed AST from a native wdl2.lark parse tree."""

    # -------------------------------------------------------------------------
    # top level: the program root and the declaration forms (include, param,
    # const). Block forms (signals, slot, waveform, sequence, mode) are added
    # to this class as those constructs are introduced.
    # -------------------------------------------------------------------------
    @v_args(meta=True)
    def start(self, meta: Meta, children: list) -> Program:
        return Program(items=tuple(children), loc=self._loc(meta))

    @v_args(meta=True)
    def include_directive(self, meta: Meta, children: list) -> Include:
        path = _str(children[0])[1:-1]  # strip the surrounding quotes
        return Include(path=path, loc=self._loc(meta))

    @v_args(meta=True)
    def param_decl(self, meta: Meta, children: list) -> ParamDecl:
        return ParamDecl(name=_str(children[0]), value=children[1], loc=self._loc(meta))

    @v_args(meta=True)
    def const_decl(self, meta: Meta, children: list) -> ConstDecl:
        return ConstDecl(name=_str(children[0]), value=children[1], loc=self._loc(meta))

    # -------------------------------------------------------------------------
    # signals block. One item per signal. A value is a slot:chan literal, a
    # bracketed group of values, or a reference to another signal name.
    # -------------------------------------------------------------------------
    @v_args(meta=True)
    def signals_block(self, meta: Meta, children: list) -> SignalsBlock:
        return SignalsBlock(items=tuple(children), loc=self._loc(meta))

    @v_args(meta=True)
    def signal_item(self, meta: Meta, children: list) -> SignalItem:
        return SignalItem(name=_str(children[0]), value=children[1], loc=self._loc(meta))

    @v_args(meta=True)
    def signal_ref(self, meta: Meta, children: list) -> SignalRef:
        return SignalRef(name=_str(children[0]), loc=self._loc(meta))

    @v_args(meta=True)
    def signal_group(self, meta: Meta, children: list) -> SignalGroup:
        return SignalGroup(members=tuple(children), loc=self._loc(meta))

    # -------------------------------------------------------------------------
    # slot block. A numbered slot of a given module kind, holding generic
    # directives in array form (`KW [args] "label"`) or key=value form.
    # -------------------------------------------------------------------------
    @v_args(meta=True)
    def slot_block(self, meta: Meta, children: list) -> SlotBlock:
        num = int(children[0])
        kind = _str(children[1])
        directives = tuple(children[2:])
        return SlotBlock(num=num, kind=kind, directives=directives, loc=self._loc(meta))

    @v_args(meta=True)
    def slot_dir_array(self, meta: Meta, children: list) -> SlotDir:
        keyword = _str(children[0])
        chan = None
        args: tuple = ()
        label = None
        for c in children[1:]:
            if isinstance(c, int):
                chan = c
            elif isinstance(c, tuple):
                args = c
            elif isinstance(c, str):
                label = c
        return SlotDir(keyword=keyword, chan=chan, args=args, label=label, loc=self._loc(meta))

    def slot_dir_chan(self, children: list) -> int:
        return int(children[0])

    def slot_dir_args(self, children: list) -> tuple:
        return children[0]  # arg_list already returns a tuple

    @v_args(meta=True)
    def slot_dir_kv(self, meta: Meta, children: list) -> SlotDir:
        keyword = _str(children[0])
        return SlotDir(
            keyword=keyword,
            chan=None,
            args=(children[1],),
            label=None,
            loc=self._loc(meta),
        )

    # -------------------------------------------------------------------------
    # waveform block. time-prefixed or bare SET statements. native waveforms
    # never contain a RETURN (the closing brace ends them), so pyext is None.
    # -------------------------------------------------------------------------
    @v_args(meta=True)
    def waveform_block(self, meta: Meta, children: list) -> WaveformBlock:
        name = _str(children[0])
        stmts = tuple(children[1:])
        return WaveformBlock(name=name, pyext=None, stmts=stmts, loc=self._loc(meta))

    @v_args(meta=True)
    def wf_timed_set(self, meta: Meta, children: list) -> WfTimedStmt:
        # children = [time, label?, set_stmt]
        time = children[0]
        label = None
        rest = children[1:]
        if rest and isinstance(rest[0], str):
            label = rest[0]
            rest = rest[1:]
        set_stmt = rest[0]
        return WfTimedStmt(time=time, label=label, sets=(set_stmt,), ret=None, loc=self._loc(meta))

    def wf_label(self, children: list) -> str:
        return _str(children[0])

    @v_args(meta=True)
    def wf_bare_set(self, meta: Meta, children: list) -> WfBareSet:
        return WfBareSet(set=children[0], loc=self._loc(meta))

    @v_args(meta=True)
    def time_relative(self, meta: Meta, children: list) -> TimeRelative:
        return TimeRelative(expr=children[0], loc=self._loc(meta))

    @v_args(meta=True)
    def time_absolute(self, meta: Meta, children: list) -> TimeAbsolute:
        return TimeAbsolute(expr=children[0], loc=self._loc(meta))

    @v_args(meta=True)
    def set_stmt(self, meta: Meta, children: list) -> SetStmt:
        # children[0] is a single target or a tuple from a target group
        target = children[0]
        target_group = None
        single: Any = None
        if isinstance(target, tuple):
            target_group = target
        else:
            single = target
        value = children[1]
        slew = children[2] if len(children) > 2 else None
        return SetStmt(
            target=single,
            target_group=target_group,
            value=value,
            slew=slew,
            loc=self._loc(meta),
        )

    def set_target_group(self, children: list) -> tuple:
        return tuple(children)

    @v_args(meta=True)
    def set_target_ref(self, meta: Meta, children: list) -> SignalRef:
        return SignalRef(name=_str(children[0]), loc=self._loc(meta))

    def set_target_slotchan(self, children: list) -> SlotChan:
        return children[0]

    @v_args(meta=True)
    def slew(self, meta: Meta, children: list) -> Slew:
        kind = _str(children[0]).upper()
        return Slew(kind=kind, loc=self._loc(meta))  # type: ignore[arg-type]

    # -------------------------------------------------------------------------
    # sequence block. explicit CALL, implicit call / ++ / --, GOTO, IF (with
    # optional `!` negation), and a bare RETURN.
    # -------------------------------------------------------------------------
    @v_args(meta=True)
    def sequence_block(self, meta: Meta, children: list) -> SequenceBlock:
        name = _str(children[0])
        stmts = tuple(children[1:])
        return SequenceBlock(name=name, stmts=stmts, loc=self._loc(meta))

    @v_args(meta=True)
    def explicit_call_stmt(self, meta: Meta, children: list) -> CallStmt:
        name = _str(children[0])
        arg = children[1] if len(children) > 1 else None
        return CallStmt(target=name, arg=arg, explicit=True, loc=self._loc(meta))

    @v_args(meta=True)
    def ident_seq_stmt(self, meta: Meta, children: list) -> Any:
        # the tail is a small tagged tuple from ident_seq_call / inc / dec
        name = _str(children[0])
        kind, payload = children[1]
        if kind == "call":
            return CallStmt(target=name, arg=payload, explicit=False, loc=self._loc(meta))
        if kind == "inc":
            return IncDec(name=name, op="++", loc=self._loc(meta))
        if kind == "dec":
            return IncDec(name=name, op="--", loc=self._loc(meta))
        raise AssertionError(f"unknown ident_seq tail: {kind}")

    def ident_seq_call(self, children: list) -> tuple:
        return ("call", children[0] if children else None)

    def ident_seq_inc(self, _children: list) -> tuple:
        return ("inc", None)

    def ident_seq_dec(self, _children: list) -> tuple:
        return ("dec", None)

    @v_args(meta=True)
    def goto_stmt(self, meta: Meta, children: list) -> GotoStmt:
        return GotoStmt(target=_str(children[0]), loc=self._loc(meta))

    @v_args(meta=True)
    def if_stmt(self, meta: Meta, children: list) -> IfStmt:
        # children = [if_neg?, CNAME, body]
        negated = False
        rest = list(children)
        if rest and rest[0] is True:
            negated = True
            rest = rest[1:]
        return IfStmt(negated=negated, param=_str(rest[0]), body=rest[1], loc=self._loc(meta))

    def if_neg(self, _children: list) -> bool:
        return True

    @v_args(meta=True)
    def return_stmt(self, meta: Meta, _children: list) -> ReturnStmt:
        return ReturnStmt(alt_name=None, loc=self._loc(meta))
