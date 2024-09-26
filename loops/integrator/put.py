# loops.integrator.put

""" Traversal adapter for PUT requests, e.g. coming from loops.agent.
"""

from zope import interface, component
from zope.cachedescriptors.property import Lazy
from zope.catalog.interfaces import ICatalog
from zope.component import adapts
from zope.container.interfaces import INameChooser
from zope.container.traversal import ContainerTraverser, ItemTraverser
from zope.contenttype import guess_content_type
from zope.event import notify
from zope.filerepresentation.interfaces import IWriteFile
from zope.interface import implementer
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.publisher.interfaces import IPublishTraverse

from cybertools.text import mimetypes
from loops.common import adapted
from loops.integrator.interfaces import IExternalSourceInfo
from loops.interfaces import IResourceManager
from loops.resource import Resource


@implementer(IPublishTraverse)
class ResourceManagerTraverser(ItemTraverser):

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
        #print('*** resources.PUT', name, path, machine, user, app)
        print('*** resources.PUT', name, path)
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
        # TODO: provide basic concept assignments (collections)
        IExternalSourceInfo(resource).externalIdentifier = identifier
        notify(ObjectCreatedEvent(resource))
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
        return name
        #return name.decode('UTF-8')


@implementer(IWriteFile)
class MetadataProxy(object):
    """ Processes a metadata file for an associated resource.
    """

    def __init__(self, resource):
        self.resource = resource

    def write(self, text):
        # TODO: provide/change concept assignments based on metadata
        print('*** metadata', repr(text))


@implementer(IWriteFile)
class DummyResource(object):
    """ Just for testing
    """

    def write(self, text):
        print('*** content', repr(text))

