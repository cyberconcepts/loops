#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
Type management stuff.

$Id$
"""

from zope.app import zapi
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope import schema
from zope.security.proxy import removeSecurityProxy
from cybertools.typology.type import BaseType, TypeManager
from cybertools.typology.interfaces import ITypeManager
from loops.interfaces import ILoopsObject, IConcept, IResource
from loops.interfaces import ITypeConcept
from loops.interfaces import IResourceAdapter, IFile, IImage, ITextDocument, INote
from loops.concept import Concept
from loops.resource import Resource, Document, MediaAsset
from loops.common import AdapterBase


class LoopsType(BaseType):

    adapts(ILoopsObject)

    factoryMapping = dict(concept=Concept, resource=Resource, document=Document)
    containerMapping = dict(concept='concepts', resource='resources')

    @Lazy
    def title(self):
        tp = self.typeProvider
        return tp is None and u'Unknown Type' or tp.title

    @Lazy
    def token(self):
        tp = self.typeProvider
        return tp is None and '.unknown' or self.root.getLoopsUri(tp)

    @Lazy
    def tokenForSearch(self):
        tp = self.typeProvider
        typeName = tp is None and 'unknown' or str(zapi.getName(tp))
        return ':'.join(('loops', self.qualifiers[0], typeName,))

    @Lazy
    def typeInterface(self):
        adapter = zapi.queryAdapter(self.typeProvider, ITypeConcept)
        if adapter is not None:
            return removeSecurityProxy(adapter.typeInterface)
        else:
            conceptType = self.typeProvider
            typeConcept = self.root.getConceptManager().getTypeConcept()
            if conceptType is typeConcept:
                return ITypeConcept
        return None

    @Lazy
    def qualifiers(self):
        ti = self.typeInterface
        if ti is None or not issubclass(ti, IResourceAdapter):
            return ('concept',)
        return ('resource',)

    @Lazy
    def factory(self):
        ti = self.typeInterface
        return self.factoryMapping.get(self.qualifiers[0], Concept)

    @Lazy
    def defaultContainer(self):
        return self.root[self.containerMapping.get(self.qualifiers[0], 'concept')]

    @Lazy
    def root(self):
        return self.context.getLoopsRoot()

    @Lazy
    def typeProvider(self):
        # TODO: unify this type attribute naming...
        return self.context.resourceType


class LoopsTypeInfo(LoopsType):
    """ The type info class used by the type manager for listing types.
    """

    def __init__(self, typeProvider):
        self.typeProvider = self.context = typeProvider


class ConceptType(LoopsType):
    """ The IType adapter for concept objects.
        Probably obsolete because all real stuff has gone to LoopsType.
    """

    adapts(IConcept)

    @Lazy
    def typeProvider(self):
        return self.context.conceptType


class ConceptTypeInfo(LoopsTypeInfo):
    """ The type info class used by the type manager for listing types.
        Probably obsolete because all real stuff has gone to LoopsTypeInfo.
    """


class ResourceType(LoopsType):
    """ The 'old-style' resource type - different classes (Document, MediaAsset)
        per type. Will be replaced by new style types that are governed by
        type concepts as is already the case for concepts.
    """

    #adapts(IResource)

    #typeTitles = {'MediaAsset': u'Media Asset'}
    typeTitles = {}

    typeInterface = None
    qualifiers = ('resource',)
    typeProvider = None

    @Lazy
    def title(self):
        cn = self.className
        return self.typeTitles.get(cn, unicode(cn))

    @Lazy
    def token(self):
        return '.'.join((self.factory.__module__, self.className))
        #cn = self.className
        #return '/'.join(('.loops/resources', cn.lower(),))

    @Lazy
    def tokenForSearch(self):
        cn = self.className
        return ':'.join(('loops:resource', cn.lower(),))

    @Lazy
    def defaultContainer(self):
        return self.root.getResourceManager()

    @Lazy
    def factory(self):
        return self.context.__class__

    @Lazy
    def className(self):
        return self.factory.__name__


class ResourceTypeInfo(ResourceType):

    def __init__(self, context, factory):
        self.context = context
        self.factory = factory


class LoopsTypeManager(TypeManager):

    adapts(ILoopsObject)

    def __init__(self, context):
        self.context = context.getLoopsRoot()

    def getType(self, token):
        if token.startswith('.loops'):
            return ConceptTypeInfo(self.context.loopsTraverse(token))
        return ResourceTypeInfo(self.context, resolve(token))

    @property
    def types(self):
        return self.conceptTypes() + self.resourceTypes()

    def listTypes(self, include=None, exclude=None):
        for t in self.types:
            if include and not [q for q in t.qualifiers if q in include]:
                continue
            if exclude and [q for q in t.qualifiers if q in exclude]:
                continue
            yield t

    def conceptTypes(self):
        cm = self.context.getConceptManager()
        to = cm.getTypeConcept()
        tp = cm.getTypePredicate()
        if to is None or tp is None:
            return ()
        result = to.getChildren([tp])
        if to not in result:
            result.append(to)
        return tuple([ConceptTypeInfo(c) for c in result])

    def resourceTypes(self):
        return tuple([ResourceTypeInfo(self.context, cls)
                        for cls in (Document,)])
                        #for cls in (Document, MediaAsset)])


class TypeConcept(AdapterBase):
    """ typeInterface adapter for concepts of type 'type'.
    """

    implements(ITypeConcept)

    _schemas = list(ITypeConcept) + list(IConcept)

    def getTypeInterface(self):
        ti = getattr(self.context, '_typeInterface', None)
        if ti is None:
            conceptType = self.context
            if conceptType == conceptType.getLoopsRoot().getConceptManager().getTypeConcept():
                return ITypeConcept
        return ti
    def setTypeInterface(self, ifc):
        self.context._typeInterface = ifc
    typeInterface = property(getTypeInterface, setTypeInterface)


class TypeInterfaceSourceList(object):

    implements(schema.interfaces.IIterableSource)

    typeInterfaces = (ITypeConcept, IFile, ITextDocument, INote)

    def __init__(self, context):
        self.context = context

    def __iter__(self):
        return iter(self.typeInterfaces)

    def __len__(self):
        return len(self.typeInterfaces)

