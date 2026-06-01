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
#     a rewrite of WDL1 as a self-contained Python compiler. Distributed
#     under the terms of the BSD 3-Clause License; see pyproject.toml.
# -----------------------------------------------------------------------------

"""Command-line entry point for the wdl2 compiler.

For now this is a stub: the package is installable and the `wdl2` command runs,
but there is nothing to build yet, so it reports that and exits non-zero. Real
argument parsing and the build command are wired up once the compiler can
produce output.
"""

from __future__ import annotations

import sys


# -----------------------------------------------------------------------------
# @fn       main
# @brief    command-line entry point named by the wdl2 console script
# @details  Stub for now: there is nothing to build, so it reports that on
#           stderr and returns a non-zero status. Argument parsing and the
#           build command arrive once the compiler can produce output.
# @param    argv   optional argument list (defaults to sys.argv[1:])
# @return   integer exit status
# -----------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    print("wdl2: nothing to build yet", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
