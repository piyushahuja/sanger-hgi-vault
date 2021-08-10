"""
Copyright (c) 2020 Genome Research Limited

Author: Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see https://www.gnu.org/licenses/
"""

import argparse

from core import typing as T
from bin.common import version


def _parser_factory():
    """ Build an argument parser meeting requirements """
    top_level = argparse.ArgumentParser("sandman")

    top_level.add_argument("vaults", metavar="PATH", type=T.Path, nargs="+",
        help="path to a Vault root directory")

    top_level.add_argument("--weaponise", action="store_true",
        help="delete expired files and perform the drain phase (i.e., don't do a dry run)")

    top_level.add_argument("--force-drain", action="store_true",
        help="drain the queue of staged files regardless of it reaching its configured threshold (requires --weaponise)")

    top_level.add_argument("--stats", metavar="FILE", type=T.Path,
        help="file listings generated by mpistat")

    top_level.add_argument("--version", action="version", version=f"%(prog)s {version.sandman}")

    def parser(args:T.List[str]) -> argparse.Namespace:
        parsed = top_level.parse_args(args)

        if parsed.force_drain and not parsed.weaponise:
            top_level.error("--force-drain can only be used with --weaponise")

        if parsed.stats is not None:
            parsed.stats = parsed.stats.resolve()

        parsed.vaults = [path.resolve() for path in parsed.vaults]

        return parsed

    return parser

parse_args = _parser_factory()
