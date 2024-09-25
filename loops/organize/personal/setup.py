# loops.organize.personal.setup

""" Automatic setup of a loops site for the organize.personal package.
"""

from zope.component import adapts

from cybertools.tracking.btree import TrackingStorage
from loops.organize.personal.favorite import Favorite
from loops.organize.personal.filter import Filter
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        records = self.context.getRecordManager()
        favorites = self.addObject(records, TrackingStorage, 'favorites',
                                   trackFactory=Favorite)
        filters = self.addObject(records, TrackingStorage, 'filters',
                                   trackFactory=Filter)
