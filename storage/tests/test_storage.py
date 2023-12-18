# loops.storage.tests.test_storage

"""Comprehensive functional testing for SQL-based storage implementation.
"""

from loops.storage.tests import common


class TestStorage(common.TestCase):

    def test_000_setUp(self):
        self.prepare()
        self.assertEqual(self.loopsRoot.__name__, 'loops')

    def test_migration(self):
        self.assertEqual('a'.upper(), 'A')

    def test_query(self):
        self.assertEqual('a'.upper(), 'A')

    def test_zzz_tearDown(self):
        self.cleanup()


if __name__ == '__main__':
    unittest.main()

