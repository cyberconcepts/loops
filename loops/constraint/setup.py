# loops.constraint.setup

""" Automatic setup of a loops site for the constraint package.
"""

from zope.component import adapts

from loops.concept import Concept
from loops.constraint.interfaces import IStaticConstraint
from loops.constraint.base import isPredicate, isType
from loops.constraint.base import hasConstraint, hasChildConstraint
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        concepts = self.context.getConceptManager()
        type = concepts.getTypeConcept()
        predicate = concepts['predicate']
        # type concepts:
        constraint = self.addAndConfigureObject(concepts, Concept,
                            'staticconstraint', title=u'Constraint',
                            conceptType=type, typeInterface=IStaticConstraint)
        self.addObject(concepts, Concept, isPredicate,
                       title=u'is Predicate for Constraint', conceptType=predicate)
        self.addObject(concepts, Concept, isType,
                       title=u'is Type for Constraint', conceptType=predicate)
        self.addObject(concepts, Concept, hasConstraint,
                       title=u'has Constraint', conceptType=predicate)
        self.addObject(concepts, Concept, hasChildConstraint,
                       title=u'has Child Constraint', conceptType=predicate)

