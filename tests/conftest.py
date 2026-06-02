# -----------------------------------------------------------------------------
# @file     conftest.py
# @brief    shared pytest fixtures
# @author   David Hale
# -----------------------------------------------------------------------------
#
# Copyright (C) 2026 California Institute of Technology
# SPDX-License-Identifier: BSD-3-Clause
#
#     This program is part of the Waveform Definition Language (WDL) version 2.
#     Distributed under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Shared pytest fixtures.

For now just the path to the committed native sample. Parser-instance fixtures
are added as the tests that consume them arrive.
"""

from __future__ import annotations

from pathlib import Path

import pytest


# -----------------------------------------------------------------------------
# @fn      native_sample_path
# @brief   path to the committed native sample exercised by test_native_sample
# @details Session-scoped. The file under tests/samples/native is the one native
#          source committed to the repo; it covers every native construct.
# @return  a Path to tests/samples/native/sample.wdl2
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session")
def native_sample_path() -> Path:
    return Path(__file__).parent / "samples" / "native" / "sample.wdl2"
