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
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.app.file.image import Image
from zope.app.file.interfaces import IFile
from zope.app.filerepresentation.interfaces import IReadFile, IWriteFile
from zope.app.size.interfaces import ISized
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from zope import schema
from persistent import Persistent
from cStringIO import StringIO

from zope.app.event.objectevent import ObjectModifiedEvent, Attributes
from zope.event import notify

from cybertools.relation.registry import getRelations
from cybertools.relation.interfaces import IRelatable
from cybertools.typology.interfaces import ITypeManager

from interfaces import IBaseResource, IResource
from interfaces import IFile, INote
from interfaces import IDocument, ITextDocument, IDocumentSchema, IDocumentView
from interfaces import IMediaAsset, IMediaAssetView
from interfaces import IResourceManager, IResourceManagerContained
from interfaces import ILoopsContained
from interfaces import IIndexAttributes
from concept import ResourceRelation
from common import ResourceAdapterBase
from view import TargetRelation

_ = MessageFactory('loops')


class Resource(Image, Contained):

    implements(IBaseResource, IResource, IResourceManagerContained, IRelatable, ISized)

    proxyInterface = IMediaAssetView

    _size = _width = _height = 0

    def __init__(self, title=u''):
        super(Resource, self).__init__()
        self.title = title

    def getResourceType(self):
        cm = self.getLoopsRoot().getConceptManager()
        typePred = cm.getTypePredicate()
        if typePred is None:
            return None
        concepts = self.getConcepts([typePred])
        # TODO (?): check for multiple types (->Error)
        return concepts and concepts[0] or cm.get('file', None)
    def setResourceType(self, concept):
        if concept is None:
            return
        current = self.getResourceType()
        if current != concept:
            typePred = self.getLoopsRoot().getConceptManager().getTypePredicate()
            if typePred is None:
                raise ValueError('No type predicate found for '
                                + zapi.getName(self))
            if current is not None:
                self.deassignConcept(current, [typePred])
            self.assignConcept(concept, typePred)
    resourceType = property(getResourceType, setResourceType)

    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    def _setData(self, data):
        dataFile = StringIO(data)  # let File tear it into pieces
        super(Resource, self)._setData(dataFile)
        if not self.contentType:
            self.guessContentType(data)
    data = property(Image._getData, _setData)

    def guessContentType(self, data):
        if not isinstance(data, str): # seems to be a file object
            data = data.read(20)
        if data.startswith('%PDF'):
            self.contentType = 'application/pdf'

    _contentType = u''
    def setContentType(self, contentType):
        if contentType:
            self._contentType = contentType
    def getContentType(self): return self._contentType
    contentType = property(getContentType, setContentType)

    def getLoopsRoot(self):
        return zapi.getParent(self).getLoopsRoot()

    def getClients(self, relationships=None):
        if relationships is None:
            relationships = [TargetRelation]
        rels = getRelations(second=self, relationships=relationships)
        return [r.first for r in rels]

    # concept relations

    def getConceptRelations (self, predicates=None, concept=None):
        predicates = predicates is None and ['*'] or predicates
        relationships = [ResourceRelation(None, self, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=concept, second=self, relationships=relationships)

    def getConcepts(self, predicates=None):
        return [r.first for r in self.getConceptRelations(predicates)]

    def assignConcept(self, concept, predicate=None):
        concept.assignResource(self, predicate)

    def deassignConcept(self, concept, predicates=None):
        concept.deassignResource(self, predicates)

    # ISized interface

    def getSize(self):
        return len(self.data)

    def sizeForSorting(self):
        return 'byte', self.getSize()

    def sizeForDisplay(self):
        return '%i Bytes' % self.getSize()


class Document(Resource):

    implements(IDocument)

    proxyInterface = IDocumentView

    def __init__(self, title=u''):
        self.title = title

    _data = u''
    def setData(self, data): self._data = data
    def getData(self): return self._data
    data = property(getData, setData)


class MediaAsset(Resource):

    implements(IMediaAsset)


class ResourceManager(BTreeContainer):

    implements(IResourceManager, ILoopsContained)

    def getLoopsRoot(self):
        return zapi.getParent(self)

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()


# adapters and similar stuff


class FileAdapter(ResourceAdapterBase):
    """ A type adapter for providing file functionality for resources.
    """

    implements(IFile)
    _schemas = list(IFile) + list(IBaseResource)


class TextDocumentAdapter(ResourceAdapterBase):
    """ A type adapter for providing text document functionality for resources.
    """

    implements(IDocument)
    _schemas = list(IDocument) + list(IBaseResource)


class NoteAdapter(ResourceAdapterBase):
    """ A type adapter for providing note functionality for resources.
    """

    implements(INote)
    _schemas = list(INote) + list(IBaseResource)


class DocumentWriteFileAdapter(object):

    implements(IWriteFile)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        ITextDocument(self.context).data = unicode(data.replace('\r', ''), 'UTF-8')
        notify(ObjectModifiedEvent(self.context, Attributes(IDocument, 'data')))


class DocumentReadFileAdapter(object):

    implements(IReadFile)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def read(self):
        return self.context.data.encode('UTF-8')

    def size(self):
        return len(self.context.data)


class IndexAttributes(object):

    implements(IIndexAttributes)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def text(self):
        context = self.context
        if not context.contentType.startswith('text'):
            return u''
        data = context.data
        if type(data) != unicode:
            data = data.decode('UTF-8')
        # TODO: transform to plain text
        #return ' '.join((zapi.getName(context), context.title, data)).strip()
        return data

    def title(self):
        context = self.context
        return ' '.join((zapi.getName(context), context.title,)).strip()


class ResourceTypeSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        self.context = context

    def __iter__(self):
        return iter(self.resourceTypes)

    @Lazy
    def resourceTypes(self):
        types = ITypeManager(self.context).listTypes(include=('resource',))
        return [t.typeProvider for t in types if t.typeProvider is not None]

    def __len__(self):
        return len(self.resourceTypes)


