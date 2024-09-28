# loops.constraint.base

""" Constraint definitions for restricting concepts and predicates available
for assignment as children or as concepts to resources.
"""

from zope.cachedescriptors.property import Lazy
from zope.interface import implementer
from zope.traversing.api import getName

from loops.common import AdapterBase, adapterAttributes, contextAttributes
from loops.constraint.interfaces import IStaticConstraint
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IStaticConstraint,)

isPredicate = 'ispredicateforconstraint'
isType = 'istypeforconstraint'
hasConstraint = 'hasconstraint'
hasChildConstraint = 'haschildconstraint'


@implementer(IStaticConstraint)
class StaticConstraint(AdapterBase):

    _contextAttributes = contextAttributes(AdapterBase, 'relationType', 'cardinality')
    _adapterAttributes = adapterAttributes(AdapterBase, 'predicates', 'types')

    def getPredicates(self):
        return self.context.getChildren([isPredicate])
    def setPredicates(self, value):
        self.context.setChildren(isPredicate, value)
    predicates = property(getPredicates, setPredicates)

    def getTypes(self):
        return self.context.getChildren([isType])
    def setTypes(self, value):
        self.context.setChildren(isType, value)
    types = property(getTypes, setTypes)
