# loops.organize.tracking.setup

""" Automatic setup of a loops site for the organize.tracking package.
"""

from zope.component import adapts

from cybertools.tracking.btree import TrackingStorage
from loops.organize.tracking.change import ChangeRecord
from loops.organize.tracking.access import AccessRecord
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        records = self.context.getRecordManager()
        changes = self.addObject(records, TrackingStorage, 'changes',
                                   trackFactory=ChangeRecord)
        access = self.addObject(records, TrackingStorage, 'access',
                                   trackFactory=AccessRecord)
