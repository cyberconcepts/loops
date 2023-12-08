'''package loops.knowledge.qualification'''

from zope.component import adapts
from zope.interface import implementer, implements
from cybertools.tracking.interfaces import ITrackingStorage
from loops.knowledge.qualification.interfaces import IQualificationRecord, \
                    IQualificationRecords
from loops.organize.work.base import WorkItem, WorkItems


class QualificationRecord(WorkItem):

    implements(IQualificationRecord)

    typeName = 'QualificationRecord'
    typeInterface = IQualificationRecord
    statesDefinition = 'knowledge.qualification'

    def doAction(self, action, userName, **kw):
        new = self.createNew(action, userName, **kw)
        new.userName = self.userName
        new.doTransition(action)
        new.reindex()
        return new


class QualificationRecords(WorkItems):
    """ A tracking storage adapter managing qualification records."""
    
    implements(IQualificationRecords) 
    adapts(ITrackingStorage)

