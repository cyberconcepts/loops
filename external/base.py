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
Reading and writing loops objects (represented by IElement objects)
in Python function notation.

$Id$
"""

from cStringIO import StringIO
import itertools
import os, sys
import zdaemon
from zope import component
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.traversing.api import getName, getParent

from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.interfaces import ISchemaFactory
from cybertools.external.base import BaseLoader
from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.external.interfaces import ILoader, IExtractor, ISubExtractor
from loops.external.element import elementTypes
from loops.interfaces import IConceptSchema, IResourceSchema, IResource, IConcept
from loops.layout.base import LayoutNode
from loops.resource import Document, MediaAsset
from loops.setup import SetupManager
from loops import util


class Base(object):

    def __init__(self, context, resourceDirectory=None):
        self.context = context
        self.resourceDirectory = resourceDirectory

    @Lazy
    def concepts(self):
        return self.context.getConceptManager()

    @Lazy
    def resources(self):
        return self.context.getResourceManager()

    @Lazy
    def views(self):
        return self.context.getViewManager()

    @Lazy
    def typeConcept(self):
        return self.concepts.getTypeConcept()

    @Lazy
    def typePredicate(self):
        return self.concepts.getTypePredicate()


class Loader(Base, BaseLoader, SetupManager):

    implements(ILoader)

    def __init__(self, context, resourceDirectory=None):
        #super(Loader, self).__init__(context, resourceDirectory)
        Base.__init__(self, context, resourceDirectory)
        BaseLoader.__init__(self, context)
        self.logger = StringIO()
        #self.logger = sys.stdout

    # TODO: care for setting attributes via Instance (Editor)
    # instead of using SetupManager methods:
    # def addConcept(self, ...):


class Extractor(Base):

    implements(IExtractor)

    count = 0

    def extract(self):
        return itertools.chain(self.extractTypes(),
                               self.extractConcepts(),
                               self.extractChildren(),
                               self.extractResources(),
                               self.extractResourceRelations(),
                               self.extractNodes(),
                              )

    def extractTypes(self):
        typeElement = elementTypes['type']
        for obj in self.typeConcept.getChildren([self.typePredicate]):
            data = self.getObjectData(obj)
            element = typeElement(getName(obj), obj.title, **data)
            self.provideSubElements(obj, element)
            self.count += 1
            yield element

    def extractConcepts(self, types=None):
        for name, obj in self.concepts.items():
            if obj.conceptType != self.typeConcept:
                if self.checkTypes(obj, types):
                    self.count += 1
                    yield self.getConceptElement(name, obj)

    def extractResources(self):
        for name, obj in self.resources.items():
            self.count += 1
            yield self.getResourceElement(name, obj)

    def extractChildren(self):
        for c in self.concepts.values():
            for r in self.getChildRelations(c):
                self.count += 1
                yield r

    def extractResourceRelations(self):
        for c in self.concepts.values():
            for r in self.getResourceRelations(c):
                self.count += 1
                yield r

    def extractNodes(self, parent=None, path=''):
        if parent is None:
            parent = self.views
        for name, obj in parent.items():
            data = {}
            for attr in ('description', 'body', 'viewName', 'pageName'):
                value = getattr(obj, attr, None)
                if value:
                    data[attr] = value
            target = obj.target
            if target is not None:
                data['target'] = '/'.join((getName(getParent(target)), getName(target)))
            elementClass = (isinstance(obj, LayoutNode) and elementTypes['layoutNode']
                                or elementTypes['node'])
            elem = elementClass(name, obj.title, path, obj.nodeType, **data)
            self.provideSubElements(obj, elem)
            self.count += 1
            yield elem
            childPath = path and '/'.join((path, name)) or name
            for elem in self.extractNodes(obj, childPath):
                #self.provideSubElements(obj, elem)
                self.count += 1
                yield elem

    def extractChanges(self, changedSince, parents=None, predicates=None,
                       types=None,):
                       #includeSubconcepts=False, includeResources=False,):
        changes = self.getChangeRecords()
        if not changes:
            return
        objects = []
        assignments = []
        deassignments = []
        tracks = changes.query(timeFrom=changedSince)
        for tr in tracks:
            obj = util.getObjectForUid(tr.taskId)
            action = tr.data.get('action')
            if action in ('add', 'modify'):
                if not self.checkTypes(obj, types):
                    continue
                if not self.checkParents(obj, parents, predicates):
                    continue
                if obj not in objects:
                    objects.append(obj)
                    name = getName(obj)
                    yield self.getConceptOrResourceElement(name, obj)
            elif action in ('assign', 'deassign'):
                pred = util.getObjectForUid(tr.data['predicate'])
                if pred == self.typePredicate:
                    continue
                child = util.getObjectForUid(tr.data['second'])
                if child is None or pred is None:
                    # may have been deleted already - can be ignored
                    continue
                if (not self.checkParents(obj, parents, predicates) and
                    not self.checkParents(child, parents, predicates)):
                    continue
                if (not self.checkTypes(obj, types) and
                    not self.checkTypes(child, types)):
                    continue
                if action == 'assign':
                    element = self.getAssignmentElement(obj, child, pred)
                else:
                    element = self.getDeassignmentElement(obj, child, pred)
                if element is not None:
                    yield element
        # TODO: include children and resources if corresponding flags are set.

    def extractForParents(self, parents, predicates=None, types=None,
                          includeSubconcepts=False, includeResources=False,):
        concepts = set(parents)
        for p in parents:
            self.collectConcepts(p, predicates, includeSubconcepts, concepts)
        conceptList = sorted(concepts, key=lambda x:
                                (x.conceptType != self.typeConcept, getName(x)))
        for c in conceptList:
            if self.checkTypes(c, types):
                self.count += 1
                yield self.getConceptElement(getName(c), c)
        for c in conceptList:
            for r in c.getChildRelations(predicates):
                if r.predicate != self.typePredicate and r.second in concepts:
                    self.count += 1
                    yield self.getChildElement(r)
        if includeResources:
            resources = set()
            for c in conceptList:
                for obj in c.getResources(predicates):
                    if obj not in resources:
                        if self.checkTypes(obj, types):
                            resources.add(obj)
                            self.count += 1
                            yield self.getResourceElement(getName(obj), obj)
            for c in conceptList:
                for r in c.getResourceRelations(predicates):
                    if r.predicate != self.typePredicate and r.second in resources:
                        self.count += 1
                        yield self.getResourceRelationElement(r)

    def collectConcepts(self, concept, predicates, includeSubconcepts, concepts):
        for obj in concept.getChildren(predicates):
            if obj not in concepts:
                concepts.add(obj)
                if includeSubconcepts:
                    self.collectConcepts(obj, predicates, includeSubconcepts,
                                         concepts)

    # helper methods

    def getChangeRecords(self):
        rm = self.context.getRecordManager()
        if rm is not None:
            return rm.get('changes')

    def checkParents(self, obj, parents, predicates):
        if not parents:
            return True
        if (not IResource.providedBy(obj) and not IConcept.providedBy(obj)):
            return False
        objParents = obj.getParents(predicates)
        for p in parents:
            if p in objParents:
                return True
        return False

    def checkTypes(self, obj, types):
        if not types:
            return True
        if (not IResource.providedBy(obj) and not IConcept.providedBy(obj)):
            return False
        return obj.getType() in types

    def getConceptOrResourceElement(self, name, obj):
        if IResource.providedBy(obj):
            return self.getResourceElement(name, obj)
        return self.getConceptElement(name, obj)

    def getAssignmentElement(self, obj, child, predicate):
        if IResource.providedBy(child):
            for r in obj.getResourceRelations([predicate], child):
                return self.getResourceRelationElement(r)
        else:
            for r in obj.getChildRelations([predicate], child):
                return self.getChildElement(r)

    def getDeassignmentElement(self, obj, child, predicate):
        args = getName(obj), getName(child), getName(predicate)
        return elementTypes['deassign'](*args)

    def getConceptElement(self, name, obj):
        if obj.conceptType is None:
            raise ValueError('Concept type is None for %s.' % getName(obj))
        data = self.getObjectData(obj)
        type = obj.conceptType
        if type == self.typeConcept:
            element = elementTypes['type'](getName(obj), obj.title, **data)
        else:
            tp = getName(type)
            element = elementTypes['concept'](name, obj.title, tp, **data)
        self.provideSubElements(obj, element)
        return element

    def getResourceElement(self, name, obj):
        data = self.getObjectData(obj, IResourceSchema)
        tp = getName(obj.resourceType)
        if isinstance(obj, Document):   # backward compatibility
            tp = 'textdocument'
        element = elementTypes['resource'](name, obj.title, tp, **data)
        element.processExport(self)
        self.provideSubElements(obj, element)
        return element

    def provideSubElements(self, obj, element):
        for name, extractor in component.getAdapters((obj,), ISubExtractor):
            for sub in extractor.extract():
                element.add(sub)

    def getChildRelations(self, c, predicates=None):
        for r in c.getChildRelations(predicates):
            if r.predicate != self.typePredicate:
                self.count += 1
                yield self.getChildElement(r)

    def getChildElement(self, r):
        args = [getName(r.first), getName(r.second), getName(r.predicate)]
        if r.order != 0 or r.relevance != 1.0:
            args.append(r.order)
        if r.relevance != 1.0:
            args.append(r.relevance)
        return elementTypes['child'](*args)

    def getResourceRelations(self, c, predicates=None):
        for r in c.getResourceRelations(predicates):
            if r.predicate != self.typePredicate:
                self.count += 1
                yield self.getResourceRelationElement(r)

    def getResourceRelationElement(self, r):
        args = [getName(r.first), getName(r.second), getName(r.predicate)]
        if r.order != 0 or r.relevance != 1.0:
            args.append(r.order)
        if r.relevance != 1.0:
            args.append(r.relevance)
        return elementTypes['resourceRelation'](*args)

    def getObjectData(self, obj, defaultInterface=IConceptSchema):
        aObj = adapted(obj)
        schemaFactory = component.getAdapter(aObj, ISchemaFactory)
        ti = IType(obj).typeInterface or defaultInterface
        schema = schemaFactory(ti, manager=self, mode='export') #, request=self.request)
        instance = IInstance(aObj)
        instance.template = schema
        # TODO:  this should also convert object attributes like e.g. typeInterface
        #data = instance.applyTemplate(mode='export')
        data = instance.applyTemplate(mode='edit')
        noexp = getattr(aObj, '_noexportAttributes', ())
        for attr in tuple(noexp) + ('title', 'name'):
            if attr in data:
                del data[attr]
        data['description'] = obj.description
        if not data['description']:
            del data['description']
        return data
