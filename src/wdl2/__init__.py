# -----------------------------------------------------------------------------
# @file     __init__.py
# @brief    WDL 2.0 compiler package
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

"""WDL 2.0 compiler package.

WDL 2.0 is a rewrite of the Waveform Definition Language as a self-contained
Python compiler including a real lexer, parser, and typed AST in place of WDL1's
regex line-matcher and external GPP preprocessor. This package is the compiler
library. The `wdl2` console script is its command-line front end.
"""

__version__ = "0.1.0.dev0"
