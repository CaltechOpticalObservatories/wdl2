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
    ConstDecl,
    FloatLit,
    IdentRef,
    Include,
    IntLit,
    ParamDecl,
    Program,
    SignalGroup,
    SignalItem,
    SignalRef,
    SignalsBlock,
    SlotBlock,
    SlotChan,
    SlotDir,
    UnaryOp,
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
