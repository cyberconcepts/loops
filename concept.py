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
Definition of the Concept and related classes.

$Id$
"""

from zope.app import zapi
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.interface import implements
from persistent import Persistent

from cybertools.relation import DyadicRelation
from cybertools.relation.registry import getRelations
from cybertools.relation.interfaces import IRelationRegistry

from interfaces import IConcept, IConceptView
from interfaces import IConceptManager, IConceptManagerContained
from interfaces import ILoopsContained


# relation classes

class ConceptRelation(DyadicRelation):
    """ A relation between concept objects.
    """


class ResourceRelation(DyadicRelation):
    """ A relation between a concept and a resource object.
    """


# concept
    
class Concept(Contained, Persistent):

    implements(IConcept, IConceptManagerContained)

    proxyInterface = IConceptView
    
    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    def __init__(self, title=u''):
        self.title = title

    def getLoopsRoot(self):
        return zapi.getParent(self).getLoopsRoot()

    # concept relations

    def getChildren(self, relationships=None):
        if relationships is None:
            relationships = [ConceptRelation]
        rels = getRelations(first=self, relationships=relationships)
        return [r.second for r in rels]
        # TODO: sort...

    def getParents(self, relationships=None):
        if relationships is None:
            relationships = [ConceptRelation]
        rels = getRelations(second=self, relationships=relationships)
        return [r.first for r in rels]

    def assignChild(self, concept, relationship=ConceptRelation):
        registry = zapi.getUtility(IRelationRegistry)
        rel = relationship(self, concept)
        registry.register(rel)
        # TODO (?): avoid duplicates

    def assignParent(self, concept, relationship=ConceptRelation):
        concept.assignChild(self, relationship)

    def deassignChildren(self, concept, relationships=None):
        if relationships is None:
            relationships = [ConceptRelation]
        registry = zapi.getUtility(IRelationRegistry)
        relations = registry.query(first=self, second=concept,
                                   relationships=relationships)
        for rel in relations:
            registry.unregister(relation)

    def deassignParents(self, concept, relationships=None):
        concept.deassignChildren(self, relationships)
    
    # resource relations

    def getResources(self, relationships=None):
        if relationships is None:
            relationships = [ResourceRelation]
        rels = getRelations(first=self, relationships=relationships)
        return [r.second for r in rels]
        # TODO: sort...

    def assignResource(self, resource, relationship=ResourceRelation):
        registry = zapi.getUtility(IRelationRegistry)
        registry.register(relationship(self, resource))
        # TODO (?): avoid duplicates

    def deassignResource(self, resource, relationships=None):
        if relationships is None:
            relationships = [ResourceRelation]
        registry = zapi.getUtility(IRelationRegistry)
        relations = registry.query(first=self, second=resource,
                                   relationships=relationships)
        for rel in relations:
            registry.unregister(relation)


# concept manager
            
class ConceptManager(BTreeContainer):

    implements(IConceptManager, ILoopsContained)

    def getLoopsRoot(self):
        return zapi.getParent(self)

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()
    
