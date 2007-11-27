#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Definition of the Concept and related classes.

$Id$
"""

from zope import component, schema
#from zope.app import zapi
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements
from zope.interface import alsoProvides, directlyProvides, directlyProvidedBy
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName, getParent
from persistent import Persistent

from cybertools.relation import DyadicRelation
from cybertools.relation.registry import getRelations
from cybertools.relation.registry import getRelationSingle, setRelationSingle
from cybertools.relation.interfaces import IRelationRegistry, IRelatable
from cybertools.typology.interfaces import IType, ITypeManager
from cybertools.util.jeep import Jeep

from loops.base import ParentInfo
from loops.interfaces import IConcept, IConceptRelation, IConceptView
from loops.interfaces import IConceptManager, IConceptManagerContained
from loops.interfaces import ILoopsContained
from loops.interfaces import IIndexAttributes
from loops import util
from loops.view import TargetRelation


# relation classes

class BaseRelation(DyadicRelation):

    def __init__(self, first, second, predicate=None):
        super(BaseRelation, self).__init__(first, second)
        if predicate is None:
            context = first is not None and first or second
            cm = context.getLoopsRoot().getConceptManager()
            predicate = cm.getDefaultPredicate()
        self.predicate = predicate

    def getPredicateName(self):
        baseName = super(BaseRelation, self).getPredicateName()
        id = util.getUidForObject(self.predicate)
        return '.'.join((baseName, id))

    # Problem with reindex catalog, needs __parent__ - but this does not help:
    #__parent__ = None
    #@property
    #def __parent__(self):
    #    return self.first
    # So we patched zope.location.location, line 109...


class ConceptRelation(BaseRelation):
    """ A relation between concept objects.
    """
    implements(IConceptRelation)


class ResourceRelation(BaseRelation):
    """ A relation between a concept and a resource object.
    """
    implements(IConceptRelation)


# concept

class Concept(Contained, Persistent):

    implements(IConcept, IConceptManagerContained, IRelatable)

    proxyInterface = IConceptView

    def __init__(self, title=u''):
        self.title = title

    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    _description = u''
    def getDescription(self): return self._description
    def setDescription(self, description): self._description = description
    description = property(getDescription, setDescription)

    def getConceptType(self):
        typePred = self.getConceptManager().getTypePredicate()
        if typePred is None:
            return None
        parents = self.getParents([typePred])
        # TODO (?): check for multiple types (->Error)
        return parents and parents[0] or None
    def setConceptType(self, concept):
        current = self.getConceptType()
        if current != concept:
            typePred = self.getConceptManager().getTypePredicate()
            if typePred is None:
                raise ValueError('No type predicate found for '
                                + getName(self))
            if current is not None:
                self.deassignParent(current, [typePred])
            self.assignParent(concept, typePred)
    conceptType = property(getConceptType, setConceptType)

    def getType(self):
        return self.conceptType

    def getLoopsRoot(self):
        return getParent(self).getLoopsRoot()

    def getConceptManager(self):
        return self.getLoopsRoot().getConceptManager()

    def getAllParents(self, collectGrants=False, result=None):
        if result is None:
            result = Jeep()
        for rel in self.getParentRelations():
            obj = rel.first
            uid = util.getUidForObject(obj)
            pi = result.get(uid)
            if pi is None:
                result[uid] = ParentInfo(obj, [rel])
                obj.getAllParents(collectGrants, result)
            elif rel not in pi.relations:
                pi.relations.append(rel)
        return result

    # concept relations

    def getClients(self, relationships=None):
        if relationships is None:
            relationships = [TargetRelation]
        rels = getRelations(second=self, relationships=relationships)
        return [r.first for r in rels]

    def getChildRelations(self, predicates=None, child=None, sort='default'):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ConceptRelation(self, None, p) for p in predicates]
        if sort == 'default':
            sort = lambda x: (x.order, x.second.title.lower())
        return sorted(getRelations(first=self, second=child, relationships=relationships),
                      key=sort)

    def getChildren(self, predicates=None, sort='default'):
        return [r.second for r in self.getChildRelations(predicates, sort=sort)]

    def getParentRelations (self, predicates=None, parent=None):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ConceptRelation(None, self, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=parent, second=self, relationships=relationships)

    def getParents(self, predicates=None):
        return [r.first for r in self.getParentRelations(predicates)]

    def assignChild(self, concept, predicate=None, order=0, relevance=1.0):
        if predicate is None:
            predicate = self.getConceptManager().getDefaultPredicate()
        registry = component.getUtility(IRelationRegistry)
        rel = ConceptRelation(self, concept, predicate)
        if order != 0:
            rel.order = order
        if relevance != 1.0:
            rel.relevance = relevance
        # TODO (?): avoid duplicates
        registry.register(rel)

    def assignParent(self, concept, predicate=None, order=0, relevance=1.0):
        concept.assignChild(self, predicate, order, relevance)

    def deassignChild(self, child, predicates=None):
        registry = component.getUtility(IRelationRegistry)
        for rel in self.getChildRelations(predicates, child):
            registry.unregister(rel)

    def deassignParent(self, parent, predicates=None):
        parent.deassignChild(self, predicates)

    # resource relations

    def getResourceRelations(self, predicates=None, resource=None):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ResourceRelation(self, None, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=self, second=resource, relationships=relationships)

    def getResources(self, predicates=None):
        return [r.second for r in self.getResourceRelations(predicates)]

    def assignResource(self, resource, predicate=None, order=0, relevance=1.0):
        if predicate is None:
            predicate = self.getConceptManager().getDefaultPredicate()
        registry = component.getUtility(IRelationRegistry)
        rel = ResourceRelation(self, resource, predicate)
        if order != 0:
            rel.order = order
        if relevance != 1.0:
            rel.relevance = relevance
        # TODO (?): avoid duplicates
        registry.register(rel)

    def deassignResource(self, resource, predicates=None):
        registry = component.getUtility(IRelationRegistry)
        for rel in self.getResourceRelations(predicates, resource):
            registry.unregister(rel)


# concept manager

class ConceptManager(BTreeContainer):

    implements(IConceptManager, ILoopsContained)

    typeConcept = None
    typePredicate = None
    defaultPredicate = None
    predicateType = None

    def getLoopsRoot(self):
        return getParent(self)

    def getAllParents(self, collectGrants=False):
        return Jeep()

    def getTypePredicate(self):
        return self.get('hasType')

    def getTypeConcept(self):
        if self.typeConcept is None:
            #self.typeConcept = self['type']
            self.typeConcept = self.get('type')
        return self.typeConcept

    def getDefaultPredicate(self):
        if self.defaultPredicate is None:
            self.defaultPredicate = self.get('standard')
        return self.defaultPredicate

    def getPredicateType(self):
        if self.predicateType is None:
            dp = self.getDefaultPredicate()
            self.predicateType = dp.conceptType
        return self.predicateType

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()


# adapters and similar components

class ConceptTypeSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        self.context = context

    def __iter__(self):
        return iter(self.conceptTypes)

    @Lazy
    def conceptTypes(self):
        types = ITypeManager(self.context).listTypes(include=('concept',))
        return [t.typeProvider for t in types]

    def __len__(self):
        return len(self.conceptTypes)


class PredicateSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        self.context = context
        self.concepts = self.context.getLoopsRoot().getConceptManager()

    def __iter__(self):
        return iter(self.predicates)

    @Lazy
    def predicates(self):
        result = []
        cm = self.concepts
        defPred = cm.getDefaultPredicate()
        typePred = cm.getTypePredicate()
        if defPred is not None and typePred is not None:
            result.append(defPred)
            #result.append(typePred)
            predType = defPred.conceptType
            if predType is not None and predType != cm.getTypeConcept():
                result.extend(p for p in predType.getChildren([typePred])
                                    if p not in result
                                       and p != typePred)
        return result

    def __len__(self):
        return len(self.conceptTypes)


class IndexAttributes(object):

    implements(IIndexAttributes)
    adapts(IConcept)

    def __init__(self, context):
        self.context = context

    def text(self):
        context = self.context
        # TODO: include attributes provided by concept type
        return ' '.join((getName(context), context.title,))

    def title(self):
        context = self.context
        return ' '.join((getName(context),
                         context.title, context.description)).strip()

