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
Definition of the View and related classses.

$Id$
"""

from zope.app import zapi
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.app.container.ordered import OrderedContainer
from zope.interface import implements
from persistent import Persistent
from cybertools.relation import DyadicRelation
from cybertools.relation.registry import IRelationsRegistry, getRelations

from interfaces import IView, INode
from interfaces import IViewManager, INodeContained
from interfaces import ILoopsContained


class View(object):

    implements(IView, INodeContained)

    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    _description = u''
    def getDescription(self): return self._description
    def setDescription(self, description): self._description = description
    description = property(getDescription, setDescription)

    def getTarget(self):
        rels = getRelations(first=self)
        if len(rels) == 0:
            return None
        if len(rels) > 1:
            raise ValueError, 'There may be only one target for a View object.'
        return rels.next().second

    def setTarget(self, target):
        return
        registry = zapi.getUtility(IRelationsRegistry)
        rels = registry.query(first=self)
        if len(rels) > 0:
            if rels[0].second != target:
                registry.unregister(target)
        else:
            rel = relationship(self, concept)
            registry.register(rel)

    target = property(getTarget, setTarget)

    def __init__(self, title=u'', description=u''):
        self.title = title
        self.description = description
        super(View, self).__init__()



class Node(View, OrderedContainer):

    implements(INode)


class ViewManager(BTreeContainer):

    implements(IViewManager, ILoopsContained)


class TargetRelation(DyadicRelation):
    """ A relation between a view and a concept or resource object.
    """

    