# loops.organize.setup

""" Automatic setup of a loops site for the organize package.
"""

from loops.concept import Concept
from loops.interfaces import ITypeConcept
from loops.organize.interfaces import IPerson, ITask
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        concepts = self.context.getConceptManager()
        type = concepts.getTypeConcept()
        predicate = concepts['predicate']

        person = self.addObject(concepts, Concept, 'person', title=u'Person',
                        conceptType=type)
        aPerson = ITypeConcept(person)
        if not aPerson.typeInterface: # allow overriding by other packages
            aPerson.typeInterface = IPerson

        owner = self.addObject(concepts, Concept, 'ownedby', title=u'owned by',
                        conceptType=predicate)
        #allocated = self.addAndConfigureObject(concepts, Concept, 'allocated',
        #                title=u'allocated',
        #                conceptType=predicate, predicateInterface=IAllocated)

        task = self.addAndConfigureObject(concepts, Concept, 'task', title=u'Task',
                        conceptType=type, typeInterface=ITask)
