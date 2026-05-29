# -----------------------------------------------------------------------------
# @file     cli.py
# @brief    command-line entry point for the wdl2 compiler
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

"""Command-line entry point.  Stub for now -- the build command is wired up
once there is something to build."""

from __future__ import annotations

import sys


# -----------------------------------------------------------------------------
# @fn     main
# @brief  command-line entry point named by the wdl2 console script
# @param  argv   optional list of arguments (defaults to sys.argv[1:])
# @return integer exit status
# -----------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    print("wdl2: nothing to build yet", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
