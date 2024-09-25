'''package loops.knowledge.qualification'''

from zope.component import adapts
from zope.interface import implementer
from cybertools.tracking.interfaces import ITrackingStorage
from loops.knowledge.qualification.interfaces import IQualificationRecord, \
                    IQualificationRecords
from loops.organize.work.base import WorkItem, WorkItems


@implementer(IQualificationRecord)
class QualificationRecord(WorkItem):

    typeName = 'QualificationRecord'
    typeInterface = IQualificationRecord
    statesDefinition = 'knowledge.qualification'

    def doAction(self, action, userName, **kw):
        new = self.createNew(action, userName, **kw)
        new.userName = self.userName
        new.doTransition(action)
        new.reindex()
        return new


@implementer(IQualificationRecords)
class QualificationRecords(WorkItems):
    """ A tracking storage adapter managing qualification records."""
    
    adapts(ITrackingStorage)

