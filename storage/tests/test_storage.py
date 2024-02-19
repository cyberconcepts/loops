# loops.storage.tests.test_storage

"""Comprehensive functional testing for SQL-based storage implementation.
"""

from loops.storage.tests import common

import transaction
from zope import component
from zope.traversing.api import getName

import config
from loops.concept import Concept
from loops.config.base import LoopsOptions
from loops.organize.personal.favorite import Favorites as FavoritesAdapter
from loops.organize.personal.interfaces import IFavorites
from loops.organize.personal.storage.favorite import Favorites
from loops.storage.migration.tracking import migrate
from loops.setup import addAndConfigureObject
from loops import util


class TestStorage(common.TestCase):

    def test_000_setUp(self):
        self.prepare()
        self.assertEqual(str(self.g.storage.engine.url),  
                         'postgresql://ccotest:cco@localhost:5432/ccotest')
        self.g.storage.dropTable('favorites')
        self.g.storage.dropTable('uid_mapping')
        component.provideAdapter(FavoritesAdapter)
        self.assertEqual(getName(self.loopsRoot), 'loops')
        self.assertEqual(getName(self.g.concepts), 'concepts')
        self.assertEqual(self.g.johnC.title, u'john')

    def test_fav_001_setUp(self):
        self.g.records = records = self.loopsRoot.getRecordManager()
        favs = IFavorites(records['favorites'])
        favs.add(self.g.resources['d001.txt'], self.g.johnC)
        self.assertEqual(len(records['favorites']), 1) 

    def test_fav_002_migration(self):
        LoopsOptions(self.loopsRoot).set('scopes.storage.schema', ['testing'])
        self.assertEqual(LoopsOptions(self.loopsRoot)('scopes.storage.schema'), 
                         ['testing'])
        migrate(self.loopsRoot, 'favorites', factory=Favorites)
        self.g.favorites = favorites = self.g.storage.create(Favorites)
        fav = favorites.get(1)
        self.assertEqual(fav.head['userName'], '102')
        favorites.storage.resetSequence('favorites', 'trackid', 101)

    def test_fav_010_add(self):
        favs = FavoritesAdapter(self.g.favorites)
        trackId = favs.add(self.g.resources['d002.txt'], self.g.johnC)
        self.assertFalse(trackId is None)
        #print('*** add, result:', trackId)

    def test_fav_020_query(self):
        favs = FavoritesAdapter(self.g.favorites)
        uid = util.getUidForObject(self.g.johnC)
        result = list(self.g.favorites.query(userName=uid))
        self.assertEqual(len(result), 2)
        self.assertEqual(list(sorted(favs.list(self.g.johnC))), [u'21', u'23'])

    def test_zzz_tearDown(self):
        transaction.commit()
        self.cleanup()


if __name__ == '__main__':
    unittest.main()

