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
Definition of the Concept class.

$Id$
"""

from zope.app import zapi
from zope.interface import implements
from persistent import Persistent

from cybertools.relation.interfaces import IRelationsRegistry
from cybertools.relation import DyadicRelation

from interfaces import IConcept


class Concept(Persistent):

    implements(IConcept)

    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    def __init__(self, name=None, title=u''):
        self.title = title

    # concept relations:

    def getSubConcepts(self, relationships=None):
        rels = getRelations(first=self, relationships=relationships)
        return [r.second for r in rels]
        # TODO: sort...

    def getParentConcepts(self, relationships=None):
        rels = getRelations(second=self, relationships=relationships)
        return [r.first for r in rels]

    def assignConcept(self, concept, relationship):
        registry = zapi.getUtility(IRelationsRegistry)
        registry.register(relationship(self, concept))
        # TODO (?): avoid duplicates

    def deassignConcept(self, concept, relationships=None):
        pass  # TODO


# TODO: move this to the relation package

def getRelations(first=None, second=None, third=None, relationships=None):
    registry = zapi.getUtility(IRelationsRegistry)
    query = {}
    if first: query['first'] = first
    if second: query['second'] = second
    if third: query['third'] = third
    if not relationships:
        return registry.query(**query)
    else:
        result = []
        for r in relationships:
            query['relationship'] = r
            result.extend(registry.query(**query))
        return result

