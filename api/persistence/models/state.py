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

from dataclasses import dataclass

from core import idm, persistence, typing as T
from api.persistence.postgres import Transaction
from .file import File


class _PersistedState(persistence.base.State):
    """ Base for our persistence operations """
    db_type:T.ClassVar[str]

    def exists(self, t:Transaction, file:File) -> T.Optional[int]:
        """
        Check the status exists for a given file

        @param   t     Transaction
        @param   file  File
        @return  The status ID, if available, or None otherwise
        """
        assert hasattr(file, "db_id")

        t.execute("""
            select id
            from   status
            where  state = %s
            and    file  = %s;
        """, (self.db_type, file.db_id))

        if (record := t.fetchone()) is None:
            return None
        return record.id

    def persist(self, t:Transaction, file:File) -> int:
        """
        Persist the status for a given file

        @param   t     Transaction
        @param   file  File
        @return  New status ID
        """
        assert hasattr(file, "db_id")

        t.execute("""
            insert into status (file, state)
            values (%s, %s)
            returning id;
        """, (file.db_id, self.db_type))
        state_id = t.fetchone().id

        # Set the notification status for all stakeholders, if required
        # (this should never happen in production)
        if self.notified:
            self.mark_notified(t, file, persistence.Anything)

        return state_id

    def mark_notified(self, t:Transaction, file:File, stakeholder:T.Union[idm.base.User, T.Type[persistence.Anything]]) -> None:
        """
        Set the notification state to true for a file and stakeholder

        @param   t            Transaction
        @param   file         File
        @param   stakeholder  Stakeholder
        """
        if (state_id := self.exists(t, file)) is None:
            state_id = self.persist(t, file)

        query_sql = """
            select id,
                   stakeholder
            from   stakeholder_notified
            where  (not notified)
            and    id   = %s
            and    file = %s
        """
        query_params = (state_id, file.db_id)

        if stakeholder != persistence.Anything:
            query_sql += """
                and stakeholder = %s
            """
            query_params += (stakeholder.uid,)

        t.execute(f"""
            insert into notifications (status, stakeholder)
            values {query_sql}
            on conflict do nothing;
        """, query_params)

    @property
    def file_cte(self) -> T.Tuple[str, T.Tuple]:
        """
        Return the SQL CTE snippet and parameters to fetch all files
        satisfying the present state
        """
        params = (self.db_type,)
        sql = """
            select file
            from   status
            where  state = %s
        """

        if self.notified != persistence.Anything:
            params += (self.notified,)
            sql += """
                and notified = %s
            """

        return sql, params


class State(T.SimpleNamespace):
    """ Namespace of file states to make importing easier """
    class Deleted(_PersistedState):
        """ File deleted """
        db_type = "deleted"

    class Staged(_PersistedState):
        """ File staged """
        db_type = "staged"

    @dataclass
    class Warned(_PersistedState):
        """ File warned for deletion """
        db_type = "warned"
        tminus:T.Union[T.TimeDelta, T.Type[persistence.Anything]]

        def exists(self, t:Transaction, file:File) -> T.Optional[int]:
            # Warnings are special, so we override the superclass
            assert hasattr(file, "db_id")
            assert self.tminus != persistence.Anything

            t.execute("""
                select status.id
                from   warnings
                join   status
                on     status.id       = warnings.status
                where  status.file     = %s
                and    warnings.tminus = %s;
            """, (file.db_id, state.tminus))

            if (record := t.fetchone()) is None:
                return None
            return record.id

        def persist(self, t:Transaction, file:File) -> int:
            # Warnings are special, so we extend the superclass
            assert hasattr(file, "db_id")
            assert self.tminus != persistence.Anything

            state_id = super().persist(t, file)
            t.execute("""
                insert into warnings (status, tminus)
                values (%s, %s);
            """, (state_id, self.tminus))

            return state_id

        @property
        def file_cte(self) -> T.Tuple[str, T.Tuple]:
            # Warnings are special, so we override the superclass
            params = (self.db_type,)
            sql = """
               select distinct status.file
               from   status
               join   warnings
               on     warnings.status = state.id
               where  status.state    = %s
            """

            if self.notified != persistence.Anything:
                params += (self.notified,)
                sql += """
                    and notified = %s
                """

            if self.tminus != persistence.Anything:
                params += (self.tminus,)
                sql += """
                    and warnings.tminus = %s
                """

            return sql, params
