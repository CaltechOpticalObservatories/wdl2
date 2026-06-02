# -----------------------------------------------------------------------------
# @file     test_native_rejects.py
# @brief    the native grammar must reject WDL1-only constructs
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2.
#     Distributed under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Native grammar must reject WDL1-only constructs.

These pin the boundary of the native language: the Python-extension hook, a
RETURN inside a waveform body, and the alternate-name RETURN form are all legal
in WDL1 (legacy) but rejected in native source.
"""

from __future__ import annotations

import pytest
from lark.exceptions import LarkError

from wdl2.compiler import native_parser


# -----------------------------------------------------------------------------
# @fn      _native_parse
# @brief   parse native source text (the tests only care whether it raises)
# @param   text   the .wdl2 source to parse
# @return  the lark parse tree
# -----------------------------------------------------------------------------
def _native_parse(text: str):
    return native_parser().parse(text)


def test_native_rejects_python_extension_syntax() -> None:
    text = """
    waveform Foo.set_nperiods(100) {
      0: set a to 1;
    }
    """
    with pytest.raises(LarkError):
        _native_parse(text)


def test_native_rejects_return_inside_waveform_body() -> None:
    text = """
    waveform Foo {
      0: set a to 1;
      return;
    }
    """
    with pytest.raises(LarkError):
        _native_parse(text)


def test_native_rejects_return_with_alternate_name() -> None:
    text = """
    sequence Foo {
      return AltName;
    }
    """
    with pytest.raises(LarkError):
        _native_parse(text)
