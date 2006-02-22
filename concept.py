#
#  Copyright (c) 2005 Helmut Merz helmutm@cy55.de
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

from zope.app import zapi
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements
from zope import schema
from zope.security.proxy import removeSecurityProxy
from persistent import Persistent

from cybertools.relation import DyadicRelation
from cybertools.relation.registry import getRelations
from cybertools.relation.registry import getRelationSingle, setRelationSingle
from cybertools.relation.interfaces import IRelationRegistry, IRelatable

from interfaces import IConcept, IConceptRelation, IConceptView
from interfaces import IConceptManager, IConceptManagerContained
from interfaces import ILoopsContained
from interfaces import ISearchableText


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
        id = zapi.getUtility(IRelationRegistry).getUniqueIdForObject(self.predicate)
        return '.'.join((baseName, str(id)))


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
    
    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    def getConceptType(self):
        typePred = self.getConceptManager().getTypePredicate()
        parents = self.getParents([typePred])
        #typeRelation = ConceptRelation(None, self, cm.getTypePredicate())
        #rels = getRelationSingle(self, typeRelation, forSecond=True)
        # TODO (?): check for multiple types (->Error)
        return parents and parents[0] or None
    def setConceptType(self, concept):
        current = self.getConceptType()
        if current != concept:
            typePred = self.getConceptManager().getTypePredicate()
            if current is not None:
                self.deassignParents(current, [typePred])
            self.assignParent(concept, typePred)
            #cm = self.getLoopsRoot().getConceptManager()
            #typeRelation = ConceptRelation(removeSecurityProxy(concept), self,
            #                               cm.getTypePredicate())
            #setRelationSingle(typeRelation, forSecond=True)
    conceptType = property(getConceptType, setConceptType)

    def __init__(self, title=u''):
        self.title = title

    def getLoopsRoot(self):
        return zapi.getParent(self).getLoopsRoot()

    def getConceptManager(self):
        return self.getLoopsRoot().getConceptManager()

    # concept relations

    def getChildRelations(self, predicates=None, second=None):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ConceptRelation(self, None, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=self, second=second, relationships=relationships)

    def getChildren(self, predicates=None):
        return [r.second for r in self.getChildRelations(predicates)]

    def getParentRelations (self, predicates=None, first=None):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ConceptRelation(None, self, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=first, second=self, relationships=relationships)
        
    def getParents(self, predicates=None):
        return [r.first for r in self.getParentRelations(predicates)]

    def assignChild(self, concept, predicate=None):
        if predicate is None:
            predicate = self.getConceptManager().getDefaultPredicate()
        registry = zapi.getUtility(IRelationRegistry)
        rel = ConceptRelation(self, concept, predicate)
        registry.register(rel)
        # TODO (?): avoid duplicates

    def assignParent(self, concept, predicate=None):
        concept.assignChild(self, predicate)

    def deassignChildren(self, concept, predicates=None):
        registry = zapi.getUtility(IRelationRegistry)
        #relations = []
        #for rs in relationships:
        #    relations.extend(registry.query(first=self, second=concept,
        #                                    relationship=rs))
        for rel in self.getChildRelations(predicates, concept):
            registry.unregister(rel)

    def deassignParents(self, concept, predicates=None):
        concept.deassignChildren(self, predicates)
    
    # resource relations

    def getResourceRelations(self, predicates=None):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ResourceRelation(self, None, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=self, relationships=relationships)

    def getResources(self, predicates=None):
        return [r.second for r in self.getResourceRelations(predicates)]

    def assignResource(self, resource, predicate=None):
        if predicate is None:
            predicate = self.getConceptManager().getDefaultPredicate()
        registry = zapi.getUtility(IRelationRegistry)
        registry.register(ResourceRelation(self, resource, predicate))
        # TODO (?): avoid duplicates

    def deassignResource(self, resource, predicates=None):
        registry = zapi.getUtility(IRelationRegistry)
        for rel in self.getResourceRelations(predicates):
            registry.unregister(rel)


# concept manager
            
class ConceptManager(BTreeContainer):

    implements(IConceptManager, ILoopsContained)

    typeConcept = None
    typePredicate = None
    defaultPredicate = None

    def getLoopsRoot(self):
        return zapi.getParent(self)

    def getTypePredicate(self):
        if self.typePredicate is None:
            self.typePredicate = self['hasType']
        return self.typePredicate

    def getTypeConcept(self):
        if self.typeConcept is None:
            self.typeConcept = self['type']
        return self.typeConcept

    def getDefaultPredicate(self):
        if self.defaultPredicate is None:
            self.defaultPredicate = self['standard']
        return self.defaultPredicate

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()
    

# adapters and similar components

class ConceptSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        #self.context = context
        self.context = removeSecurityProxy(context)
        root = self.context.getLoopsRoot()
        self.concepts = root.getConceptManager()

    def __iter__(self):
        for obj in self.concepts.values():
            yield obj

    def __len__(self):
        return len(self.concepts)


class ConceptTypeSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        self.context = context
        #self.context = removeSecurityProxy(context)
        root = self.context.getLoopsRoot()
        self.concepts = root.getConceptManager()

    def __iter__(self):
        return iter(self.conceptTypes)

    @Lazy
    def conceptTypes(self):
        result = []
        cm = self.concepts
        typeObject = cm.getTypeConcept()
        unknownType = self.concepts.get('unknown')
        if typeObject is not None:
            typeRelation = ConceptRelation(None, typeObject, cm.getTypePredicate())
            types = typeObject.getChildren((typeRelation,))
            if typeObject not in types:
                result.append(typeObject)
            if unknownType is not None and unknownType not in types:
                result.append(unknownType)
            result.extend(types)
        return result

    def __len__(self):
        return len(self.conceptTypes)


class SearchableText(object):

    implements(ISearchableText)
    adapts(IConcept)

    def __init__(self, context):
        self.context = context

    def searchableText(self):
        context = self.context
        return ' '.join((zapi.getName(context), context.title,))

