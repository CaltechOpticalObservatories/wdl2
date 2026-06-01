# -----------------------------------------------------------------------------
# @file     __init__.py
# @brief    typed abstract syntax tree for WDL 2.0
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

"""Typed abstract syntax tree for WDL 2.0.

Defines the node types every parse produces (nodes.py), the source-location
record carried on each node (source.py), and the lark transformers that build
the typed tree from a parse tree (transform.py).
"""
