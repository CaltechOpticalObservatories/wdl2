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

stub-only. wires argument parser so `wdl2 --help` and the `build`
subcommand exist, but build is not yet implemented.
"""

from __future__ import annotations

import argparse
import sys


# -----------------------------------------------------------------------------
# @fn      build_parser
# @brief   construct the argument parser for the wdl2 command
# @details Declares the `build` subcommand with a source-file argument and a
#          --legacy flag. The subcommand is recognized but not yet implemented.
# @return  a configured argparse.ArgumentParser
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wdl2", description="WDL 2.0 compiler")
    sub = p.add_subparsers(dest="command", metavar="<command>")

    build = sub.add_parser("build", help="(not yet implemented) compile a .wdl2 source")
    build.add_argument("source", help="path to .wdl2 source file")
    build.add_argument("--legacy", action="store_true", help="ingest a WDL1 multi-file project")

    return p


# -----------------------------------------------------------------------------
# @fn      main
# @brief   command-line entry point named by the wdl2 console script
# @details stub only, accepts any subcommand
# @param   argv   optional argument list (defaults to sys.argv[1:])
# @return  integer exit status
# -----------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    print(f"wdl2: command {args.command!r} not yet implemented", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
