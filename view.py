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
Definition of the View and related classses.

$Id$
"""

from zope import component
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.app.container.ordered import OrderedContainer
from zope.cachedescriptors.property import Lazy, readproperty
from zope.component import adapts
from zope.interface import implements
from zope.interface import alsoProvides, directlyProvides, directlyProvidedBy
from zope.intid.interfaces import IIntIds
from zope.publisher.browser import applySkin
from zope import schema
from zope.security import canAccess
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName, getParent
from persistent import Persistent

from cybertools.composer.layout.base import LayoutManager
from cybertools.relation import DyadicRelation
from cybertools.relation.registry import getRelations
from cybertools.relation.interfaces import IRelationRegistry, IRelatable
from cybertools.util.jeep import Jeep
from loops.base import ParentInfo
from loops.common import AdapterBase
from loops.interfaces import IView, INode, INodeSchema, INodeAdapter
from loops.interfaces import IViewManager, INodeContained
from loops.interfaces import ILoopsContained
from loops.interfaces import ITargetRelation
from loops.interfaces import IConcept
from loops.versioning.util import getVersion
from loops import util
from loops.util import _


class View(object):

    implements(IView, INodeContained, IRelatable)

    def __init__(self, title=u'', description=u''):
        self.title = title
        self.description = description
        super(View, self).__init__()

    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    _description = u''
    def getDescription(self): return self._description
    def setDescription(self, description): self._description = description
    description = property(getDescription, setDescription)

    _viewName = u''
    def getViewName(self):
        return self._viewName
    def setViewName(self, viewName):
        self._viewName = viewName
    viewName = property(getViewName, setViewName)

    def getTarget(self):
        rels = getRelations(first=self, relationships=[TargetRelation])
        if len(rels) == 0:
            return None
        if len(rels) > 1:
            raise ValueError('There may be only one target for a View object: %s - %s'
                % (getName(self), `[getName(r.second) for r in rels]`))
        return list(rels)[0].second

    def setTarget(self, target):
        registry = component.getUtility(IRelationRegistry)
        rels = list(registry.query(first=self, relationship=TargetRelation))
        if len(rels) > 0:
            oldRel = rels[0]
            if oldRel.second == target:
                return
            else:
                registry.unregister(oldRel)
        if target:
            targetSchema = target.proxyInterface
            rel = TargetRelation(self, target)
            registry.register(rel)
            alsoProvides(self, targetSchema)

    target = property(getTarget, setTarget)

    def getLoopsRoot(self):
        return getParent(self).getLoopsRoot()

    def getAllParents(self, collectGrants=False):
        return Jeep()


class Node(View, OrderedContainer):

    implements(INode)

    _nodeType = 'info'
    def getNodeType(self): return self._nodeType
    def setNodeType(self, nodeType): self._nodeType = nodeType
    nodeType = property(getNodeType, setNodeType)

    _body = u''
    def getBody(self): return self._body
    def setBody(self, body): self._body = body
    body = property(getBody, setBody)

    contentType = u'zope.source.rest'

    def getParentNode(self, nodeTypes=None):
        parent = getParent(self)
        while INode.providedBy(parent):
            if not nodeTypes or parent.nodeType in nodeTypes:
                return parent
            parent = getParent(parent)
        return None

    def getAllParents(self, collectGrants=False):
        result = Jeep()
        parent = self.getParentNode()
        while parent is not None:
            result[util.getUidForObject(parent)] = ParentInfo(parent)
            parent = parent.getParentNode()
        return result

    def getChildNodes(self, nodeTypes=None):
        for item in self.values():
            if not canAccess(item, 'title'):
                continue
            if INode.providedBy(item) \
                    and (not nodeTypes or item.nodeType in nodeTypes):
                yield item
            else:
                continue

    def getMenu(self):
        if self.nodeType == 'menu':
            return self
        return self.getParentNode(['menu'])

    def getPage(self):
        pageTypes = ['page', 'menu', 'info']
        if self.nodeType in pageTypes:
            return self
        return self.getParentNode(pageTypes)

    def getMenuItems(self):
        return self.getChildNodes(['page', 'menu'])

    def getPageItems(self):
        return self.getChildNodes(['page', 'menu', 'info'])

    def getTextItems(self):
        return self.getChildNodes(['text'])

    def isMenuItem(self):
        return self.nodeType in ('page', 'menu')


class ViewManager(OrderedContainer):

    implements(IViewManager, ILoopsContained)

    def getLoopsRoot(self):
        return getParent(self)

    def getViewManager(self):
        return self

    def getAllParents(self, collectGrants=False):
        return Jeep()


class TargetRelation(DyadicRelation):
    """ A relation between a view and its target.
    """
    implements(ITargetRelation)


# adapters

class NodeAdapter(AdapterBase):
    """ Allows nodes to be adapted like concepts and resources, e.g.
        for i18n (needs derivation from I18NAdapterBase),
        specific capabilities or dynamic attributes.
    """

    implements(INodeAdapter)
    adapts(INode)

    _contextAttributes = ('title', 'description', 'body',)


nodeTypes = [
        ('text', _(u'Text')), # shown as part of an enclosing page
        ('page', _(u'Page')), # standalone page with a menu item
        ('menu', _(u'Menu')), # top-level menu (also a page)
        ('info', _(u'Info')), # not shown automatically, but may be a link target
]

class NodeTypeSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        self.context = context

    def __contains__(self, token):
        return token in [t[0] for t in nodeTypes]

    def __iter__(self):
        return iter(nodeTypes)

    def __len__(self):
        return len(nodeTypes)
