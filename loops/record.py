# loops.record

""" Definition of the RecordManager class.
"""

from zope.container.btree import BTreeContainer
from zope.interface import implementer
from zope.traversing.api import getParent

from cybertools.util.jeep import Jeep
from loops.interfaces import ILoopsContained
from loops.interfaces import IRecordManager


@implementer(IRecordManager, ILoopsContained)
class RecordManager(BTreeContainer):

    title = 'records'

    def getLoopsRoot(self):
        return getParent(self)

    def getAllParents(self, collectGrants=False):
        return Jeep()

