# loops.organize.process.setup

""" Automatic setup of a loops site for the process package.
"""

from zope.component import adapts

from cybertools.process.interfaces import IProcess
from loops.concept import Concept
from loops.interfaces import ITypeConcept
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        concepts = self.context.getConceptManager()
        type = concepts.getTypeConcept()
        predicate = concepts['predicate']
        # type concepts:
        process = self.addObject(concepts, Concept, 'process', title=u'Process',
                                 conceptType=type)
        processTypeAdapter = ITypeConcept(process)
        if not processTypeAdapter.typeInterface:
            processTypeAdapter.typeInterface = IProcess
        # predicates:
        follows = self.addObject(concepts, Concept, 'follows', title=u'follows',
                        conceptType=predicate)


