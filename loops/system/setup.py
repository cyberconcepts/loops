# loops.system.setup

""" Automatic setup of a loops site for the system package.
"""

from zope.component import adapts

from cybertools.tracking.btree import TrackingStorage
from loops.concept import Concept
from loops.interfaces import ITypeConcept
from loops.setup import SetupManager as BaseSetupManager
from loops.system.job import JobRecord


class SetupManager(BaseSetupManager):

    def setup(self):
        concepts = self.context.getConceptManager()
        type = concepts.getTypeConcept()
        predicate = concepts['predicate']
        # type concepts:
        job = self.addAndConfigureObject(concepts, Concept, 'job', title=u'Job',
                        conceptType=type)
        # job records:
        records = self.context.getRecordManager()
        if 'jobs' not in records:
            records['jobs'] = TrackingStorage(trackFactory=JobRecord)

