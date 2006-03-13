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
from cybertools.typology.type import BaseType, TypeManager
from loops.interfaces import ILoopsObject, IConcept, IResource
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


class LoopsTypeInfo(LoopsType):
    """ A common class the instances of which are used as a generic type info.
    """

    def __init__(self, typeProvider):
        self.typeProvider = self.context = typeProvider


class ConceptType(LoopsType):
    """ The type adapter for concept objects.
    """

    adapts(IConcept)

    qualifiers = ('concept',)

    @Lazy
    def typeProvider(self):
        return self.context.conceptType


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
        cn = self.className
        return '/'.join(('.loops/resources', cn.lower(),))

    @Lazy
    def tokenForSearch(self):
        cn = self.className
        return ':'.join(('loops:resource', cn.lower(),))

    @Lazy
    def className(self):
        return self.context.__class__.__name__



class ResourceTypeInfo(ResourceType):

    def __init__(self, cls):
        self.cls = cls

    @Lazy
    def className(self):
        return self.cls.__name__


class LoopsTypeManager(TypeManager):

    adapts(ILoopsObject)

    def __init__(self, context):
        self.context = context.getLoopsRoot()

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
        return tuple([ResourceTypeInfo(cls) for cls in (Document, MediaAsset)])
