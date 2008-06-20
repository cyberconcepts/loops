#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Basic implementation of the elements used for the intermediate format for export
and import of loops objects.

$Id$
"""

import os
from zope import component
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.interface import Interface, implements
from zope.traversing.api import getName, traverse

from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.interfaces import ISchemaFactory
from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.interfaces import IConceptSchema
from loops.external.interfaces import IElement
from loops.i18n.common import I18NValue


class Element(dict):

    implements(IElement)

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
                         if k not in self.posArgs)
        # use IInstance adapter (name='editor') for unmarshalling values
        #self.object = loader.addConcept(self['name'], self['title'], type, **kw)
        self.object = loader.addConcept(self['name'], self['title'], type)
        formState = self.getInstance().applyTemplate(data=kw, ignoreValidation=True)

    def getInstance(self, omit=['title']):
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
            if not isinstance(ti, basestring):
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


class ChildElement(Element):

    elementType = 'child'
    posArgs = ('first', 'second', 'predicate', 'order', 'relevance')

    def __init__(self, *args):
        for idx, arg in enumerate(args):
            self[self.posArgs[idx]] = arg

    def execute(self, loader):
        loader.assignChild(self['first'], self['second'], self['predicate'])


class ResourceElement(Element):

    elementType = 'resource'
    posArgs = ('name', 'title', 'type')

    def processExport(self, extractor):
        content = self.pop('data', '')
        fileFlags = 'wb'
        if (self.get('contentType', '').startswith('text/')
            and isinstance(content, unicode)):
            content = content.encode('UTF-8')
            fileFlags = 'wt'
        dataPath = os.path.join(extractor.resourceDirectory, self['name'])
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
        loader.assignResource(self['first'], self['second'], self['predicate'])


class NodeElement(Element):

    elementType = 'node'
    posArgs = ('name', 'title', 'path', 'type')

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
        node = loader.addNode(self['name'], self['title'], cont, type, **kw)
        #if target is not None:
        #    targetObject = traverse(loader.context, target, None)
        #    node.target = targetObject
        #self.object = node


# element registry

elementTypes = dict(
    type=TypeElement,
    concept=ConceptElement,
    child=ChildElement,
    resource=ResourceElement,
    resourceRelation=ResourceRelationElement,
    node=NodeElement,
    I18NValue=I18NValue,
)

toplevelElements = ('type', 'concept', 'resource',
                    'child', 'resourceRelation', 'node')
