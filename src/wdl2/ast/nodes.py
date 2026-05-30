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
#     a rewrite of WDL1 as a self-contained Python compiler.  Distributed
#     under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Typed AST nodes for WDL 2.0.

One frozen dataclass per construct.  Every node carries a SrcLoc.  Both the
native and the legacy transformer build their trees from this one shared set
of nodes, so the constructs are introduced here as the language grows.
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
    """Base class for every AST node.  The source location is keyword-only so
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
# visitor base
# -----------------------------------------------------------------------------

class Visitor:
    """Generic tree walker.  Dispatch is on a node's concrete class name:
    override visit_<ClassName> for the nodes of interest, and anything else
    falls through to generic_visit, which recurses over the dataclass fields.
    """

    # -------------------------------------------------------------------------
    # @fn     visit
    # @brief  dispatch to visit_<ClassName>, or generic_visit when absent
    # @param  node   the AST node to visit
    # @return whatever the dispatched method returns
    # -------------------------------------------------------------------------
    def visit(self, node: Node):
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is None:
            return self.generic_visit(node)
        return method(node)

    # -------------------------------------------------------------------------
    # @fn     generic_visit
    # @brief  default visit -- recurse over every field except the source loc
    # @param  node   the AST node whose children are visited
    # @return None
    # -------------------------------------------------------------------------
    def generic_visit(self, node: Node):
        for f in fields(node):
            if f.name == "loc":
                continue
            value = getattr(node, f.name)
            self._visit_value(value)

    # -------------------------------------------------------------------------
    # @fn     _visit_value
    # @brief  visit one field value, descending into nodes and tuples of nodes
    # @param  value   a field value pulled from a node
    # @return None
    # -------------------------------------------------------------------------
    def _visit_value(self, value) -> None:
        if isinstance(value, Node):
            self.visit(value)
        elif isinstance(value, tuple):
            for item in value:
                self._visit_value(item)
