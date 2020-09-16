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

import sys

import core.vault
from api.logging import log
from api.persistence import Persistence, models
from api.vault import Branch, Vault
from bin.common import config, idm
from core import typing as T
from core.persistence import Anything, Filter
from core.utils import human_size


# Staged and notified persisted state
_StagedAndNotified = models.State.Staged(notified=True)


class HandlerBusy(Exception):
    """ Raised when the downstream handler is busy """

class DownstreamFull(Exception):
    """ Raised when the downstream handler reports it's out of capacity """


def _create_vault(relative_to:T.Path) -> Vault:
    # Defensively create a vault with the common IdM
    try:
        return Vault(relative_to, idm=idm)

    except core.vault.exception.VaultConflict as e:
        # Non-managed file(s) exists where the vault should be
        log.error(f"Skipping {relative_to}: {e}")


def main(argv:T.List[str] = sys.argv):
    log.info("FOR DEMONSTRATION PURPOSES ONLY")

    vault_dirs = argv[1:]
    if len(vault_dirs) == 0:
        log.critical("You must provide at least one path that resolves to a vault")
        sys.exit(1)

    persistence = Persistence(config.persistence, idm)

    # STEP 1 - For all given vaults:
    # * Move all "archived" files into the "staged" branch
    # * Record this in the DB appropriately ("staged queue")
    # * Delete the external counterpart
    for vault_dir in map(T.Path, vault_dirs):
        if not vault_dir.exists():
            log.error(f"Skipping {vault_dir}: Not found")
            continue

        vault = _create_vault(vault_dir)

        # TODO The stuff...


    # STEP 2 - Drain the staged queue, no matter what size, into the
    # archive handler, following the appropriate interface.
    criteria = Filter(state       = _StagedAndNotified,
                      stakeholder = Anything)
    try:
        with persistence.files(criteria) as staged_queue:
            # NOTE If the downstream handler returns a non-zero exit
            # code, we MUST raise an error in this block, otherwise the
            # queue will be cleared automatically regardless
            queue = staged_queue.accumulator
            log.info(f"Checking downstream handler is ready for {human_size(queue.size)}B...")

            # TODO The stuff...

    except HandlerBusy:
        log.warning("The downstream handler is busy; try again later...")

    except DownstreamFull:
        log.error("The downstream handler is reporting it is out of capacity and cannot proceed")


if __name__ == "__main__":
    main()
