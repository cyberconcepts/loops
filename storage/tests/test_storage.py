# loops.storage.tests.test_storage

"""Comprehensive functional testing for SQL-based storage implementation.
"""

import transaction
from zope import component
from zope.traversing.api import getName

from loops.concept import Concept
from loops.config.base import LoopsOptions
from loops.organize.personal.favorite import Favorites as FavoritesFolder
from loops.organize.personal.interfaces import IFavorites
from loops.organize.personal.storage.favorite import Favorites
from loops.organize.tracking.storage.migration import migrate
from loops.setup import addAndConfigureObject
from loops.storage.tests import common


class TestStorage(common.TestCase):

    def test_000_setUp(self):
        self.prepare()
        self.assertEqual(getName(self.loopsRoot), 'loops')
        person = self.loopsRoot['concepts']['person']
        component.provideAdapter(FavoritesFolder)

    def test_fav_001_setUp(self):
        self.assertEqual(getName(self.g.concepts), 'concepts')
        self.assertEqual(self.g.johnC.title, u'john')
        self.g.records = records = self.loopsRoot.getRecordManager()
        self.g.favorites = records['favorites']
        self.g.fav = IFavorites(self.g.favorites)
        self.g.fav.add(self.g.resources['d001.txt'], self.g.johnC)
        self.assertEqual(len(self.g.favorites), 1) 

    def test_fav_002_migration(self):
        import config
        self.assertEqual(config.dbname, 'ccotest')
        self.assertEqual(config.dbuser, 'ccotest')
        LoopsOptions(self.loopsRoot).set('cco.storage.schema', ['testing'])
        self.assertEqual(LoopsOptions(self.loopsRoot)('cco.storage.schema'), ['testing'])
        migrate(self.loopsRoot, 'favorites', factory=Favorites)
        transaction.commit()

    def test_query(self):
        self.assertEqual('a'.upper(), 'A')

    def test_zzz_tearDown(self):
        self.cleanup()


if __name__ == '__main__':
    unittest.main()

