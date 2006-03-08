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
from loops.interfaces import ILoopsObject, IConcept


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

    @Lazy
    def typeProvider(self):
        return self.context.conceptType


class LoopsTypeManager(TypeManager):

    adapts(ILoopsObject)

    def __init__(self, context):
        self.context = context.getLoopsRoot()

    @property    
    def types(self):
        cm = self.context.getConceptManager()
        to = cm.getTypeConcept()
        tp = cm.getTypePredicate()
        if to is None or tp is None:
            return ()
        result = to.getChildren([tp])
        if to not in result:
            result.append(to)
        return tuple(LoopsTypeInfo(c) for c in result)


