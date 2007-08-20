#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Traversal adapter for PUT requests, e.g. coming from loops.agent.

$Id$
"""

from zope import interface, component
from zope.interface import implements
from zope.component import adapts
from zope.app.container.traversal import ContainerTraverser, ItemTraverser
from zope.cachedescriptors.property import Lazy
from zope.filerepresentation.interfaces import IWriteFile
from zope.publisher.interfaces import IPublishTraverse

from loops.interfaces import IResourceManager


class ResourceManagerTraverser(ItemTraverser):

    implements(IPublishTraverse)
    adapts(IResourceManager)

    def publishTraverse(self, request, name):
        if request.method == 'PUT':
            if name.startswith('.'):
                stack = request._traversal_stack
                #stack = request.getTraversalStack()
                #print '*** resources.PUT', name, '/'.join(stack)
                machine, user, app = stack.pop(), stack.pop(), stack.pop()
                path = '/'.join(reversed(stack))
                path = path.replace(',', ',,').replace('/', ',')
                for i in range(len(stack)):
                    stack.pop()
                print '*** resources.PUT', name, path, machine, user, app
                return DummyWriteFile()
        return super(ResourceManagerTraverser, self).publishTraverse(request, name)


class DummyWriteFile(object):

    implements(IWriteFile)

    def write(self, text):
        print '*** content', repr(text)

