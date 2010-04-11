#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.app.container.interfaces import IAdding
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.component.interfaces import ObjectEvent
from zope.dublincore.interfaces import IZopeDublinCore
from zope.event import notify
from zope.interface import implements
from zope.interface import alsoProvides, directlyProvides, directlyProvidedBy
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.security.proxy import removeSecurityProxy, isinstance
from zope.traversing.api import getName, getParent
from persistent import Persistent

from cybertools.meta.interfaces import IOptions
from cybertools.relation import DyadicRelation
from cybertools.relation.registry import getRelations
from cybertools.relation.interfaces import IRelationRegistry, IRelatable
from cybertools.typology.interfaces import IType, ITypeManager
from cybertools.util.jeep import Jeep

from loops.base import ParentInfo
from loops.common import adapted, AdapterBase
from loops.i18n.common import I18NValue
from loops.interfaces import IConcept, IConceptRelation, IConceptView
from loops.interfaces import IConceptManager, IConceptManagerContained
from loops.interfaces import ILoopsContained
from loops.interfaces import IIndexAttributes
from loops.interfaces import IAssignmentEvent, IDeassignmentEvent
from loops.security.common import canListObject
from loops import util
from loops.versioning.util import getMaster
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

    workspaceInformation = None

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
        parents = self.getParents([typePred], noSecurityCheck=True)
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

    def setType(self, value):
        self.conceptType = value

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

    def getLongTitle(self):
        return self.title

    # concept relations

    def getClients(self, relationships=None):
        if relationships is None:
            relationships = [TargetRelation]
        rels = getRelations(second=self, relationships=relationships)
        return [r.first for r in rels if canListObject(r.first)]

    def getChildRelations(self, predicates=None, child=None, sort='default',
                          noSecurityCheck=False):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ConceptRelation(self, None, p) for p in predicates]
        if sort == 'default':
            sort = lambda x: (x.order, x.second.title.lower())
        rels = (r for r in getRelations(self, child, relationships=relationships)
                  if canListObject(r.second, noSecurityCheck))
        return sorted(rels, key=sort)

    def getChildren(self, predicates=None, sort='default', noSecurityCheck=False):
        return [r.second for r in self.getChildRelations(predicates, sort=sort,
                                                noSecurityCheck=noSecurityCheck)]

    def getParentRelations (self, predicates=None, parent=None, sort='default',
                            noSecurityCheck=False):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ConceptRelation(None, self, p) for p in predicates]
        if sort == 'default':
            sort = lambda x: (x.order, x.first.title.lower())
        rels = (r for r in getRelations(parent, self, relationships=relationships)
                  if canListObject(r.first, noSecurityCheck))
        return sorted(rels, key=sort)

    def getParents(self, predicates=None, sort='default', noSecurityCheck=False):
        return [r.first for r in self.getParentRelations(predicates, sort=sort,
                                                noSecurityCheck=noSecurityCheck)]

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
        notify(AssignmentEvent(self, rel))

    def setChildren(self, predicate, concepts):
        existing = self.getChildren([predicate])
        for c in existing:
            if c not in concepts:
                self.deassignChild(c, [predicate])
        for c in concepts:
            if c not in existing:
                self.assignChild(c, predicate)

    def assignParent(self, concept, predicate=None, order=0, relevance=1.0):
        concept.assignChild(self, predicate, order, relevance)

    def setParents(self, predicate, concepts):
        existing = self.getParents([predicate])
        for c in existing:
            if c not in concepts:
                self.deassignParent(c, [predicate])
        for c in concepts:
            if c not in existing:
                self.assignParent(c, predicate)

    def deassignChild(self, child, predicates=None, order=None, noSecurityCheck=False):
        registry = component.getUtility(IRelationRegistry)
        for rel in self.getChildRelations(predicates, child,
                                          noSecurityCheck=noSecurityCheck):
            if order is None or rel.order == order:
                registry.unregister(rel)
                notify(DeassignmentEvent(self, rel))

    def deassignParent(self, parent, predicates=None, noSecurityCheck=False):
        parent.deassignChild(self, predicates)

    # resource relations

    def getResourceRelations(self, predicates=None, resource=None, sort='default',
                             noSecurityCheck=False):
        #if resource is not None:
        #    resource = getMaster(resource)
        predicates = predicates is None and ['*'] or predicates
        relationships = [ResourceRelation(self, None, p) for p in predicates]
        if sort == 'default':
            sort = lambda x: (x.order, x.second.title.lower())
        rels = (r for r in getRelations(self, resource, relationships=relationships)
                  if canListObject(r.second, noSecurityCheck))
        return sorted(rels, key=sort)

    def getResources(self, predicates=None, sort='default', noSecurityCheck=False):
        return [r.second for r in self.getResourceRelations(predicates, sort=sort,
                                                noSecurityCheck=noSecurityCheck)]

    def assignResource(self, resource, predicate=None, order=0, relevance=1.0):
        resource = getMaster(resource)
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
        notify(AssignmentEvent(self, rel))

    def deassignResource(self, resource, predicates=None, order=None):
        resource = getMaster(resource)
        registry = component.getUtility(IRelationRegistry)
        for rel in self.getResourceRelations(predicates, resource):
            if order is None or rel.order == order:
                registry.unregister(rel)
                notify(DeassignmentEvent(self, rel))

    # combined children+resources query

    def getChildAndResourceRelations(self, predicates=None, sort='default'):
        if predicates is None:
            predicates = [self.getConceptManager().getDefaultPredicate()]
        relationships = ([ResourceRelation(self, None, p) for p in predicates]
                       + [ConceptRelation(None, self, p) for p in predicates])
        if sort == 'default':
            sort = lambda x: (x.order, x.second.title.lower())
        rels = (r for r in getRelations(self, child, relationships=relationships)
                  if canListObject(r.second))
        return sorted(rels, key=sort)


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
        if IBrowserRequest.providedBy(context):
            context = context.context
        if IAdding.providedBy(context):
            context = context.context
        if isinstance(context, AdapterBase):
            context = context.context
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
            predType = defPred.conceptType
            if predType is not None and predType != cm.getTypeConcept():
                result.extend(p for p in predType.getChildren([typePred])
                                    if p not in result
                                       and p != typePred)
        return result

    def __len__(self):
        return len(self.predicates)


class IndexAttributes(object):

    implements(IIndexAttributes)
    adapts(IConcept)

    def __init__(self, context):
        self.context = context

    @Lazy
    def adapted(self):
        return adapted(self.context)

    @Lazy
    def adaptedIndexAttributes(self):
        if self.adapted != self.context:
            #return component.queryAdapter(self.adapted, IIndexAttributes)
            return IIndexAttributes(self.adapted, None)

    def text(self):
        if self.adaptedIndexAttributes is not None:
            return self.adaptedIndexAttributes.text()
        description = self.context.description
        if isinstance(description, I18NValue):
            description = ' '.join(description.values())
        actx = self.adapted
        indexAttrs = getattr(actx, '_textIndexAttributes', ())
        indexValues = [getattr(actx, attr, u'???') for attr in indexAttrs]
        return ' '.join([self.title(), description] +
                        [c for c in self.creators() if c is not None] +
                        [v for v in indexValues if v is not None]).strip()

    def title(self):
        context = self.context
        title = context.title
        if isinstance(title, I18NValue):
            title = ' '.join(title.values())
        return ' '.join((getName(context), title)).strip()

    def date(self):
        if self.adaptedIndexAttributes is not None:
            return self.adaptedIndexAttributes.date()

    def creators(self):
        cr = IZopeDublinCore(self.context).creators or []
        pau = component.getUtility(IAuthentication)
        creators = []
        for c in cr:
            try:
                principal = pau.getPrincipal(c)
                creators.append(principal.title)
            except PrincipalLookupError:
                creators.append(c)
        return creators

    def identifier(self):
        id = getattr(self.adapted, 'identifier', None)
        if id is None:
            return getName(self.context)
        return id

    def keywords(self):
        if self.adaptedIndexAttributes is not None:
            return self.adaptedIndexAttributes.keywords()

# events

class AssignmentEvent(ObjectEvent):

    implements(IAssignmentEvent)

    def __init__(self, obj, relation):
        super(AssignmentEvent, self).__init__(obj)
        self.relation = relation


class DeassignmentEvent(ObjectEvent):

    implements(IDeassignmentEvent)

    def __init__(self, obj, relation):
        super(DeassignmentEvent, self).__init__(obj)
        self.relation = relation
