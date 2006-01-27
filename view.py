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
from zope.app.container.traversal import ContainerTraverser, ItemTraverser
from zope.app.container.traversal import ContainerTraversable
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements
from zope.security.proxy import removeSecurityProxy
from persistent import Persistent
from cybertools.relation import DyadicRelation
from cybertools.relation.registry import IRelationsRegistry, getRelations

from interfaces import IView, INode, INodeConfigSchema
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
        rels = getRelations(first=self, relationships=[TargetRelation])
        if len(rels) == 0:
            return None
        if len(rels) > 1:
            raise ValueError, 'There may be only one target for a View object.'
        return list(rels)[0].second

    def setTarget(self, target):
        registry = zapi.getUtility(IRelationsRegistry)
        rels = list(registry.query(first=self, relationship=TargetRelation))
        if len(rels) > 0:
            oldRel = rels[0]
            if oldRel.second is target:
                return
            else:
                registry.unregister(oldRel)
        rel = TargetRelation(self, target)
        registry.register(rel)

    target = property(getTarget, setTarget)

    def __init__(self, title=u'', description=u''):
        self.title = title
        self.description = description
        super(View, self).__init__()

    def getLoopsRoot(self):
        return zapi.getParent(self).getLoopsRoot()


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
        parent = zapi.getParent(self)
        while INode.providedBy(parent):
            if not nodeTypes or parent.nodeType in nodeTypes:
                return parent
            parent = zapi.getParent(parent)
        return None

    def getChildNodes(self, nodeTypes=None):
        for item in self.values():
            if INode.providedBy(item) \
                    and (not nodeTypes or item.nodeType in nodeTypes):
                yield item
            else:
                continue

    def getMenu(self):
        return self.nodeType == 'menu' and self or self.getParentNode(['menu'])

    def getPage(self):
        pageTypes = ['page', 'menu', 'info']
        if self.nodeType in pageTypes:
            return self
        return self.getParentNode(pageTypes)

    def getMenuItems(self):
        return self.getChildNodes(['page', 'menu'])

    def getTextItems(self):
        return self.getChildNodes(['text'])


class ViewManager(OrderedContainer):

    implements(IViewManager, ILoopsContained)

    def getLoopsRoot(self):
        return zapi.getParent(self)


class TargetRelation(DyadicRelation):
    """ A relation between a view and another object.
    """

# adapters

class NodeTraverser(ItemTraverser):

    adapts(INode)

    def publishTraverse(self, request, name):
        if name == '.loops':
            return self.context.getLoopsRoot()
        return super(NodeTraverser, self).publishTraverse(request, name)
 

class NodeConfigAdapter(object):

    def __init__(self, context):
        self.context = removeSecurityProxy(context)
        self._targetType = None

    implements(INodeConfigSchema)
    adapts(INode)

    # provide access to fields of the Node class:

    def getTitle(self): return self.context.title
    def setTitle(self, title): self.context.title = title
    title = property(getTitle, setTitle)

    def getDescription(self): return self.context.description
    def setDescription(self, description): self.context.description = description
    description = property(getDescription, setDescription)
    
    def getNodeType(self): return self.context.nodeType
    def setNodeType(self, nodeType): self.context.nodeType = nodeType
    nodeType = property(getNodeType, setNodeType)

    # the real config stuff:
    
    @Lazy
    def loopsRoot(self): return self.context.getLoopsRoot()

    def getTargetUri(self):
        rootPath = zapi.getPath(self.loopsRoot)
        if self.context.target is not None:
            path = zapi.getPath(self.context.target)[len(rootPath):]
            return '.loops' + path
        else:
            return ''
    
    def setTargetUri(self, uri):
        names = uri.split('/')
        if names[0] == '.loops':
            path = '/'.join(names[1:])
            self.context.target = zapi.traverse(self.loopsRoot, path)
            
    targetUri = property(getTargetUri, setTargetUri)

    def getTargetType(self):
        target = self.context.target
        if target:
            return '%s.%s' % (target.__module__, target.__class__.__name__)
        return None
    def setTargetType(self, tt):
        pass  # only used whe a new target object is created
    targetType = property(getTargetType, setTargetType)

    createTarget = False  # not used

