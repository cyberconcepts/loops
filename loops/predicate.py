# loops.predicate

""" Definition and management of special predicates and corresponding relations.
"""

from zope import component, schema
from zope.component import adapts
from zope.interface import implementer
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName

from loops.interfaces import ILoopsObject, IConcept, IResource, IConceptRelation
from loops.interfaces import IPredicate, IRelationAdapter
from loops.interfaces import IIsSubtype     #, IMappingAttributeRelation
from loops.concept import Concept
from loops.common import adapted, AdapterBase
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IPredicate,)


@implementer(IPredicate)
class Predicate(AdapterBase):
    """ typeInterface adapter for concepts of type 'predicate'.
    """

    _contextAttributes = list(IPredicate) # + list(IConcept)

    def getOptions(self):
        return getattr(self.context, '_options', [])
    def setOptions(self, value):
        self.context._options = value
    options = property(getOptions, setOptions)


class PredicateInterfaceSourceList(TypeInterfaceSourceList):
    """ Collects type interfaces for predicates, i.e. interfaces that
        may be used for specifying additional attributes of relations.
    """

    predicateInterfaces = ()

    @property
    def typeInterfaces(self):
        return self.predicateInterfaces


@implementer(IRelationAdapter)
class RelationAdapter(AdapterBase):
    """ Base class for adapters to relations that may be used for
        specifying additional attributes for relations.
    """

    adapts(IConceptRelation)


def adaptedRelation(relation):
    if isinstance(relation, RelationAdapter):
        return obj
    ifc = adapted(relation.predicate).predicateInterface
    if ifc is not None:
        adRelation = component.queryAdapter(relation, ifc)
        if adRelation is not None:
            return adRelation
    return relation


# standard relation adapters

PredicateInterfaceSourceList.predicateInterfaces += (
        IIsSubtype,)

@implementer(IIsSubtype)
class IsSubtype(RelationAdapter):
    """ Allows specification of a predicate for relations between concepts
        of certain types.
    """

    _contextAttributes = list(IIsSubtype)


#PredicateInterfaceSourceList.predicateInterfaces += (IMappingAttributeRelation,)

#@implementer(IMappingAttributeRelation)
#class MappingAttributeRelation(AdapterBase):

    #_contextAttributes = list(IMappingAttributeRelation)
