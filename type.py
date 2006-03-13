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
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from cybertools.typology.type import BaseType, TypeManager
from loops.interfaces import ILoopsObject, IConcept, IResource
from loops.concept import Concept
from loops.resource import Document, MediaAsset


class LoopsType(BaseType):

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
        return ':'.join(('loops:concept', typeName,))

    @Lazy
    def root(self):
        return self.context.getLoopsRoot()


class ConceptType(LoopsType):
    """ The type adapter for concept objects.
    """

    adapts(IConcept)

    qualifiers = ('concept',)
    factory = Concept

    @Lazy
    def typeProvider(self):
        return self.context.conceptType

    @Lazy
    def defaultContainer(self):
        return self.root.getConceptManager()


class ConceptTypeInfo(ConceptType):

    def __init__(self, typeProvider):
        self.typeProvider = self.context = typeProvider


class ResourceType(LoopsType):

    adapts(IResource)

    typeTitles = {'MediaAsset': u'Media Asset'}

    qualifiers = ('resource',)

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
                        for cls in (Document, MediaAsset)])
