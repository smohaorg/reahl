# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function, unicode_literals, absolute_import, division
from contextlib import contextmanager

from reahl.tofu import Fixture, set_up, tear_down, Fixture, uses
from reahl.sqlalchemysupport import metadata, Session

from reahl.dev.fixtures import ReahlSystemFunctionFixture


@uses(reahl_system_fixture=ReahlSystemFunctionFixture)
class SqlAlchemyFixture(Fixture):
    commit = False

    @set_up
    def start_transaction(self):
        if not self.commit:
            # The tests run in a nested transaction inside a real transaction, and both are rolled back
            # This is done because finalise_session (real code) is run as part of the test, and it
            # checks for the nested transaction and behaves differently to make testing possible.
            # Session.begin() - this happens implicitly
            Session.begin_nested()

    @tear_down
    def finalise_transaction(self):
        if not self.commit:
            self.reahl_system_fixture.system_control.rollback()  # The nested one
            self.reahl_system_fixture.system_control.rollback()  # The real transaction
            self.reahl_system_fixture.system_control.finalise_session()  # To nuke the session, and commit (possibly nothing)
        else:
            self.reahl_system_fixture.system_control.commit()  # The nested one
            self.reahl_system_fixture.system_control.commit()  # The real transaction

    @contextmanager
    def persistent_test_classes(self, *entities):
        try:
            self.create_test_tables()
            yield
        finally:
            self.destroy_test_tables(*entities)

    def create_test_tables(self):
        metadata.create_all(bind=Session.connection())

    def destroy_test_tables(self, *entities):
        # Session.flush()
        Session.expunge_all()
        for entity in entities:
            if hasattr(entity, '__table__'):
                entity.__table__.metadata.remove(entity.__table__)
                # noinspection PyProtectedMember
                if entity.__name__ in entity._decl_class_registry:
                    # noinspection PyProtectedMember
                    del entity._decl_class_registry[entity.__name__]


