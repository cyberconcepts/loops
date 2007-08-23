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
from zope.app.catalog.interfaces import ICatalog
from zope.app.container.interfaces import INameChooser
from zope.app.container.traversal import ContainerTraverser, ItemTraverser
from zope.contenttype import guess_content_type
from zope.cachedescriptors.property import Lazy
from zope.event import notify
from zope.filerepresentation.interfaces import IWriteFile
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.publisher.interfaces import IPublishTraverse

from cybertools.text import mimetypes
from loops.common import adapted
from loops.integrator.interfaces import IExternalSourceInfo
from loops.interfaces import IResourceManager
from loops.resource import Resource


class ResourceManagerTraverser(ItemTraverser):

    implements(IPublishTraverse)
    adapts(IResourceManager)

    def publishTraverse(self, request, name):
        if request.method == 'PUT':
            if name.startswith('.'):
                return self.getOrCreateResource(request, name)
        return super(ResourceManagerTraverser, self).publishTraverse(request, name)

    def getOrCreateResource(self, request, name):
        stack = request._traversal_stack
        #machine, user, app = stack.pop(), stack.pop(), stack.pop()
        path = '/'.join(reversed(stack))
        #path = path.replace(',', ',,').replace('/', ',')
        for i in range(len(stack)):
            # prevent further traversal
            stack.pop()
        #print '*** resources.PUT', name, path, machine, user, app
        print '*** resources.PUT', name, path
        resource = self.findResource(path)
        if resource is None:
            resource = self.createResource(path)
        notify(ObjectModifiedEvent(resource))
        #resource = DummyResource()
        if name == '.meta':
            return MetadataProxy(resource)
        return resource

    def findResource(self, identifier):
        cat = component.getUtility(ICatalog)
        loopsRoot = self.context.getLoopsRoot()
        result = cat.searchResults(
                    loops_externalidentifier=(identifier, identifier))
        result = [r for r in result if r.getLoopsRoot() == loopsRoot]
        if len(result) > 1:
            raise ValueError('More than one resource found for external '
                    'identifier %s. Resources found: %s.' %
                    (identifier, str([r.name for r in result])))
        if len(result) == 0:
            return None
        return result[0]

    def createResource(self, identifier):
        name = self.generateName(identifier)
        title = self.generateTitle(identifier)
        contentType = guess_content_type(identifier,
                        default='application/octet-stream')[0]
        resource = Resource()
        self.context[name] = resource
        cm = self.context.getLoopsRoot().getConceptManager()
        resource.resourceType = cm['extfile']
        obj = adapted(resource)
        obj.contentType = contentType
        obj.title = title
        #obj.data = data
        notify(ObjectModifiedEvent(resource))
        # TODO: provide basic concept assignments (collections)
        IExternalSourceInfo(resource).externalIdentifier == identifier
        return resource

    def generateName(self, name):
        name = INameChooser(self.context).chooseName(name, None)
        return name

    def generateTitle(self, name):
        separators = ('/', '\\')
        for sep in separators:
            if sep in name:
                name = name.rsplit(sep, 1)[-1]
                break
        if '.' in name:
            base, ext = name.rsplit('.', 1)
            if ext.lower() in mimetypes.extensions.values():
                name = base
        return name.decode('UTF-8')


class MetadataProxy(object):
    """ Processes a metadata file for an associated resource.
    """

    def __init__(self, resource):
        self.resource = resource

    implements(IWriteFile)

    def write(self, text):
        # TODO: provide/change concept assignments based on metadata
        print '*** metadata', repr(text)


class DummyResource(object):
    """ Just for testing
    """

    implements(IWriteFile)

    def write(self, text):
        print '*** content', repr(text)

