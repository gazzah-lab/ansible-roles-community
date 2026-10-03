"""Identity planning regressions; no system accounts are modified."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('migration', Path(__file__).parents[1] / 'plugins/modules/accounts_migrate.py')
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


class MigrationPlanTest(unittest.TestCase):
    def test_release_uid_before_new_account(self):
        users = [dict(name='aymen.gazzah', uid=1000), dict(name='sysmoudir', uid=2000)]
        existing = dict(sysmoudir=SimpleNamespace(pw_uid=1000, pw_dir='/home/sysmoudir'))
        plan = migration.plan_changes(users, [], existing, {}, '')
        self.assertEqual(plan, [dict(kind='uid', name='sysmoudir', old=1000, new=2000)])

    def test_uid_cycle_is_planned(self):
        existing = {name: SimpleNamespace(pw_uid=uid, pw_dir='/home/' + name) for name, uid in [('one', 1000), ('two', 2000)]}
        plan = migration.plan_changes([dict(name='one', uid=2000), dict(name='two', uid=1000)], [], existing, {}, '')
        self.assertEqual(len(plan), 2)

    def test_unmanaged_collision_refused(self):
        existing = dict(other=SimpleNamespace(pw_uid=1000, pw_dir='/home/other'))
        with self.assertRaisesRegex(ValueError, 'unmanaged'):
            migration.plan_changes([dict(name='new', uid=1000)], [], existing, {}, '')

    def test_connection_account_migration_refused(self):
        existing = dict(ansible=SimpleNamespace(pw_uid=3000, pw_dir='/var/lib/ansible'))
        with self.assertRaisesRegex(ValueError, 'connection account'):
            migration.plan_changes([dict(name='ansible', uid=3001)], [], existing, {}, 'ansible')

    def test_idempotent(self):
        existing = dict(sysmoudir=SimpleNamespace(pw_uid=2000, pw_dir='/var/lib/sysmoudir'))
        self.assertEqual(migration.plan_changes([dict(name='sysmoudir', uid=2000)], [], existing, {}, ''), [])


if __name__ == '__main__':
    unittest.main()
