"""
Copyright (c) 2019, 2020 Genome Research Limited

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

from datetime import datetime, timedelta, timezone

now     = lambda: datetime.now(timezone.utc)
epoch   = lambda ts: datetime.fromtimestamp(ts, timezone.utc)
to_utc  = lambda dt: dt.astimezone(timezone.utc)
timestamp = lambda dt: int(to_utc(dt).timestamp())

delta   = timedelta
seconds = lambda d: d.total_seconds()

ISO8601 = "%Y-%m-%dT%H:%M:%SZ%z"
