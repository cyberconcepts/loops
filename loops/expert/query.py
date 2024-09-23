#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
Generic query functionality for retrieving stuff from a loops database.
"""

from BTrees.IIBTree import IITreeSet
from BTrees.IFBTree import IFBucket, IFBTree, IFTreeSet
from BTrees.IOBTree import IOBucket, IOBTree
from zope import interface, component
from zope.component import adapts
from zope.interface import implements, implementer
from zope.cachedescriptors.property import Lazy
from zope.intid.interfaces import IIntIds

from cybertools.catalog.query import Term, Eq, Between, And, Or
from cybertools.catalog.query import Text as BaseText
from cybertools.catalog.query import AllOf, AnyOf
from loops.expert.interfaces import IQuery
from loops.security.common import canListObject
from loops import util

titleIndex = ('', 'loops_title')
textIndex = ('', 'loops_text')
typeIndex = ('', 'loops_type')
identifierIndex = ('', 'loops_identifier')
stateIndex = ('', 'loops_state')
keywordsIndex = ('', 'loops_keywords')


# standard text/field/keyword index queries

@implementer(IQuery)
def Title(value):
    return BaseText(titleIndex, value)

@implementer(IQuery)
def Text(value):
    return BaseText(textIndex, value)

@implementer(IQuery)
def Identifier(value):
    if value.endswith('*'):
        v1 = value[:-1]
        v2 = value[:-1] + '\x7f'
        return Between(identifierIndex, v1, v2)
    return Eq(identifierIndex, value)

@implementer(IQuery)
def Type(value):
    if value.endswith('*'):
        v1 = value[:-1]
        v2 = value[:-1] + '\x7f'
        return Between(typeIndex, v1, v2)
    return Eq(typeIndex, value)

@implementer(IQuery)
def State(statesDefinition, value):
    if not isinstance(value, (list, tuple)):
        value = [value]
    return AnyOf(stateIndex, [':'.join((statesDefinition, v)) for v in value])

@implementer(IQuery)
def AllKeywords(value):
    if not isinstance(value, (list, tuple)):
        value = [value]
    return AllOf(keywordsIndex, value)

@implementer(IQuery)
def AnyKeyword(value):
    if not isinstance(value, (list, tuple)):
        value = [value]
    return AnyOf(keywordsIndex, value)


# concept map queries

class ConceptMapTerm(Term):

    implements(IQuery)

    def __init__(self, concept, **kw):
        self.context = concept
        for k, v in kw.items():
            setattr(self, k, v)


class Resources(ConceptMapTerm):

    predicates = None

    def apply(self):
        result = IFTreeSet()
        for r in self.context.getResources():
            result.insert(int(util.getUidForObject(r)))
        return result


class Children(ConceptMapTerm):

    includeResources = False
    recursive = False
    predicates = None

    def apply(self):
        result = IFTreeSet()
        self.getRecursive(self.context, result)
        return result

    def getRecursive(self, c, result):
        if self.includeResources:
            for r in c.getResources():
                uid = int(util.getUidForObject(r))
                if uid not in result:
                    result.insert(uid)
        for c in c.getChildren():
            uid = int(util.getUidForObject(c))
            if uid not in result:
                result.insert(uid)
                if self.recursive:
                    self.getRecursive(c, result)


# utility functions

def getObjects(uids, root=None, checkPermission=canListObject):
    intIds = component.getUtility(IIntIds)
    for uid in uids:
        obj = util.getObjectForUid(uid, intIds)
        if ((root is None or obj.getLoopsRoot() == root) and
            (checkPermission is None or checkPermission(obj))):
            yield obj
