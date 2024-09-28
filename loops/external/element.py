# loops.external.element

""" Basic implementation of the elements used for the intermediate format for export
and import of loops objects.
"""

import os
from zope import component
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.interface import Interface, implementer
from zope.traversing.api import getName, traverse

from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.interfaces import ISchemaFactory
from cybertools.tracking.btree import TrackingStorage
from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.external.interfaces import IElement
from loops.interfaces import IConceptSchema
from loops.i18n.common import I18NValue
from loops.layout.base import LayoutNode
from loops.predicate import adaptedRelation
from loops.view import Node


@implementer(IElement)
class Element(dict):

    elementType = ''
    posArgs = ()
    object = None
    parent = None
    subElements = None

    def __init__(self, name, title, type=None, *args, **kw):
        self['name'] = name
        self['title'] = title
        if type:
            self['type'] = type
        for k, v in kw.items():
            self[k] = v

    def __getitem__(self, key):
        if isinstance(key, Element):
            key = (key,)
        if isinstance(key, tuple):
            for item in key:
                item.parent = self
                self.add(item)
            return key
        return super(Element, self).__getitem__(key)

    def processExport(self, extractor):
        pass

    def add(self, element):
        if self.subElements is None:
            self.subElements = []
        self.subElements.append(element)

    def execute(self, loader):
        pass


class ConceptElement(Element):

    elementType = 'concept'
    posArgs = ('name', 'title', 'type')

    def execute(self, loader):
        type = loader.concepts[self['type']]
        kw = dict((k, v) for k, v in self.items()
                         #if k not in self.posArgs)
                         if k not in ['name', 'type'])
        self.object = loader.addConcept(self['name'], self['title'], type)
        formState = self.getInstance().applyTemplate(data=kw, ignoreValidation=True)
        # simple hack for resolving interface definition:
        pi = self.get('predicateInterface')
        if pi:
            adapted(self.object).predicateInterface = resolve(pi)

    #def getInstance(self, omit=['title']):
    def getInstance(self, omit=[]):
        adObject = adapted(self.object)
        schemaFactory = ISchemaFactory(adObject)
        ti = IType(self.object).typeInterface or IConceptSchema
        instance = component.getAdapter(adObject, IInstance, name='editor')
        instance.template = schemaFactory(ti, manager=self, omit=omit)
        return instance


class TypeElement(ConceptElement):

    elementType = 'type'
    posArgs = ('name', 'title')

    def __init__(self, name, title, *args, **kw):
        super(TypeElement, self).__init__(name, title, *args, **kw)
        ti = self.get('typeInterface')
        if ti:
            if not isinstance(ti, str):
                self['typeInterface'] = '.'.join((ti.__module__, ti.__name__))

    def execute(self, loader):
        kw = dict((k, v) for k, v in self.items()
                if k not in ('name', 'title', 'type', 'typeInterface'))
        ti = self.get('typeInterface')
        if ti:
            kw['typeInterface'] = resolve(ti)
        self.object = loader.addConcept(self['name'], self['title'],
                            loader.typeConcept, **kw)
        instance = self.getInstance(omit=['title', 'typeInterface'])
        formState = instance.applyTemplate(data=kw, ignoreValidation=True)
        if ti:
            # overwrite type interface, might have been ignored in addConcept
            adapted(self.object).typeInterface = kw['typeInterface']


class RecordManagerElement(Element):

    elementType = 'records'
    posArgs = ('name', 'trackFactory')

    def __init__(self, name, trackFactory, **kw):
        self['name'] = name
        tf = self['trackFactory'] = trackFactory
        if not isinstance(tf, str):
            self['trackFactory'] = '.'.join((tf.__module__, tf.__name__))
        for k, v in kw.items():
            self[k] = v

    def execute(self, loader):
        name = self['name']
        tf = resolve(self['trackFactory'])
        records = loader.context.getRecordManager()
        obj = records.get(name)
        if obj is None:
            obj = records[name] = TrackingStorage(trackFactory=tf)
        else:
            obj.trackFactory = tf
            obj.indexAttributes = tf.index_attributes
            obj.setupIndexes()
        self.object = obj


class ChildElement(Element):

    elementType = 'child'
    posArgs = ('first', 'second', 'predicate', 'order', 'relevance')

    def __init__(self, *args, **kw):
        for idx, arg in enumerate(args):
            self[self.posArgs[idx]] = arg
        for k, v in kw.items():
            self[k] = v

    def execute(self, loader):
        loader.assignChild(self['first'], self['second'], self['predicate'],
                           order = self.get('order') or 0,
                           relevance = self.get('relevance') or 1.0)
        additionalParams = [(k, v) for k, v in self.items()
                                   if k not in self.posArgs]
        if additionalParams:
            pred = loader.getPredicate(self['predicate'])
            first = loader.concepts[self['first']]
            second = loader.concepts[self['second']]
            relation = first.getChildRelations([pred], child=second)[0]
            adaptedRel = adaptedRelation(relation)
            for attr, value in additionalParams:
                setattr(adaptedRel, attr, value)


class ResourceElement(Element):

    elementType = 'resource'
    posArgs = ('name', 'title', 'type')

    def processExport(self, extractor):
        content = self.pop('data', '')
        fileFlags = 'wb'
        if self.get('contentType', '').startswith('text/'):
            fileFlags = 'wt'
        elif isinstance(content, str):
            content = content.encode('UTF-8')
        directory = extractor.resourceDirectory
        if not os.path.exists(directory):
            os.makedirs(directory)
        dataPath = os.path.join(directory, self['name'])
        f = open(dataPath, fileFlags)
        f.write(content)
        f.close()

    def execute(self, loader):
        type = loader.concepts[self['type']]
        kw = dict((k, v) for k, v in self.items()
                         if k not in self.posArgs)
        dataPath = os.path.join(loader.resourceDirectory, self['name'])
        if os.path.exists(dataPath):
            ct = self.get('contentType', '')
            flag = ct.startswith('text/') and 'r' or 'rb'
            f = open(dataPath, flag)
            content = f.read()
            if ct.startswith('text/'):
                content = content.decode('UTF-8')
            kw['data'] = content
            f.close()
        self.object = loader.addResource(self['name'], self['title'], type, **kw)


class ResourceRelationElement(ChildElement):

    elementType = 'resourceRelation'

    def execute(self, loader):
        loader.assignResource(self['first'], self['second'], self['predicate'],
                           order = self.get('order') or 0,
                           relevance = self.get('relevance') or 1.0)


class DeassignmentElement(Element):

    elementType = 'deassign'
    posArgs = ('first', 'second', 'predicate')

    def __init__(self, *args, **kw):
        for idx, arg in enumerate(args):
            self[self.posArgs[idx]] = arg
        for k, v in kw.items():
            self[k] = v

    def execute(self, loader):
        if self.get('type') in ('child', 'concept'):
            loader.deassignChild(self['first'], self['second'], self['predicate'])
        else:
            loader.deassignResource(self['first'], self['second'], self['predicate'])


class NodeElement(Element):

    elementType = 'node'
    posArgs = ('name', 'title', 'path', 'type')
    factory = Node

    def __init__(self, *args, **kw):
        for idx, arg in enumerate(args):
            self[self.posArgs[idx]] = arg
        for k, v in kw.items():
            self[k] = v

    def execute(self, loader):
        type = self['type']
        cont = traverse(loader.views, self['path'])
        #target = self.pop('target', None)
        kw = dict((k, v) for k, v in self.items()
                         if k not in self.posArgs)
        node = loader.addNode(self['name'], self['title'], cont, type,
                              factory=self.factory, **kw)
        #if target is not None:
        #    targetObject = traverse(loader.context, target, None)
        #    node.target = targetObject
        #self.object = node


class LayoutNodeElement(NodeElement):

    elementType = 'layoutNode'
    factory = LayoutNode


# element registry

elementTypes = dict(
    type=TypeElement,
    concept=ConceptElement,
    records=RecordManagerElement,
    child=ChildElement,
    resource=ResourceElement,
    resourceRelation=ResourceRelationElement,
    deassign=DeassignmentElement,
    node=NodeElement,
    layoutNode=LayoutNodeElement,
    I18NValue=I18NValue,
)

toplevelElements = ('type', 'concept', 'resource', 'records',
                    'child', 'resourceRelation', 'node', 'deassign')
