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

class ConceptRelation(DyadicRelation):
    """ A relation between concept objects.
    """
    implements(IConceptRelation)

    def __init__(self, first, second, predicate=None):
        super(ConceptRelation, self).__init__(first, second)
        if predicate is None:
            context = first is not None and first or second
            cm = context.getLoopsRoot().getConceptManager()
            predicate = cm.getDefaultPredicate()
        self.predicate = predicate

    def getPredicateName(self):
        baseName = super(ConceptRelation, self).getPredicateName()
        id = zapi.getUtility(IRelationRegistry).getUniqueIdForObject(self.predicate)
        return '.'.join((baseName, str(id)))


class ResourceRelation(DyadicRelation):
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
        cm = self.getLoopsRoot().getConceptManager()
        typeRelation = ConceptRelation(None, self, cm.getTypePredicate())
        rel = getRelationSingle(self, typeRelation, forSecond=True)
        return rel and rel.first or None
    def setConceptType(self, concept):
        if self.getConceptType() != concept:
            cm = self.getLoopsRoot().getConceptManager()
            typeRelation = ConceptRelation(removeSecurityProxy(concept), self,
                                           cm.getTypePredicate())
            setRelationSingle(typeRelation, forSecond=True)
    conceptType = property(getConceptType, setConceptType)

    def __init__(self, title=u''):
        self.title = title

    def getLoopsRoot(self):
        return zapi.getParent(self).getLoopsRoot()

    # concept relations

    def getChildren(self, relationships=None):
        if relationships is None:
            relationships = [ConceptRelation(self, None)]
        rels = getRelations(first=self, relationships=relationships)
        return [r.second for r in rels]
        # TODO: sort...

    def getParents(self, relationships=None):
        if relationships is None:
            relationships = [ConceptRelation(None, self)]
        rels = getRelations(second=self, relationships=relationships)
        return [r.first for r in rels]

    def assignChild(self, concept, relationship=ConceptRelation):
        registry = zapi.getUtility(IRelationRegistry)
        rel = relationship(self, concept)
        registry.register(rel)
        # TODO (?): avoid duplicates

    def assignParent(self, concept, relationship=ConceptRelation):
        concept.assignChild(self, relationship)

    def deassignChildren(self, concept, relationships=None):
        if relationships is None:
            relationships = [ConceptRelation(self, None)]
        registry = zapi.getUtility(IRelationRegistry)
        relations = []
        for rs in relationships:
            relations.extend(registry.query(first=self, second=concept,
                                            relationship=rs))
        for rel in relations:
            registry.unregister(rel)

    def deassignParents(self, concept, relationships=None):
        concept.deassignChildren(self, relationships)
    
    # resource relations

    def getResources(self, relationships=None):
        if relationships is None:
            relationships = [ResourceRelation]
        rels = getRelations(first=self, relationships=relationships)
        return [r.second for r in rels]
        # TODO: sort...

    def assignResource(self, resource, relationship=ResourceRelation):
        registry = zapi.getUtility(IRelationRegistry)
        registry.register(relationship(self, resource))
        # TODO (?): avoid duplicates

    def deassignResource(self, resource, relationships=None):
        if relationships is None:
            relationships = [ResourceRelation]
        registry = zapi.getUtility(IRelationRegistry)
        relations = registry.query(first=self, second=resource,
                                   relationships=relationships)
        for rel in relations:
            registry.unregister(relation)


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

