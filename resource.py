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
from zope.app.file.image import Image as BaseMediaAsset
from zope.app.file.interfaces import IFile
from zope.app.filerepresentation.interfaces import IReadFile, IWriteFile
from zope.app.size.interfaces import ISized
from zope.component import adapts
from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from persistent import Persistent
from cStringIO import StringIO

from textindexng.interfaces import IIndexableContent
from textindexng.content import IndexContentCollector
from cybertools.relation.registry import getRelations
from cybertools.relation.interfaces import IRelatable

from interfaces import IResource
from interfaces import IDocument, IDocumentSchema, IDocumentView
from interfaces import IMediaAsset, IMediaAssetSchema, IMediaAssetView
from interfaces import IResourceManager, IResourceManagerContained
from interfaces import ILoopsContained
from interfaces import IIndexAttributes
from concept import ResourceRelation
from view import TargetRelation

_ = MessageFactory('loops')


class Resource(Contained, Persistent):

    implements(IResource, IResourceManagerContained, IRelatable)

    _size = _width = _height = 0

    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    _contentType = ''
    def setContentType(self, contentType):
        if contentType:
            self._contentType = contentType
    def getContentType(self): return self._contentType
    contentType = property(getContentType, setContentType)

    def __init__(self, title=u''):
        self.title = title

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


class Document(Resource):

    implements(IDocument, ISized)

    proxyInterface = IDocumentView

    _data = u''
    def setData(self, data): self._data = data
    def getData(self): return self._data
    data = property(getData, setData)

    def getSize(self):
        return len(self.data)

    def sizeForSorting(self):
        return 'byte', self.getSize()

    def sizeForDisplay(self):
        return '%i Bytes' % self.getSize()


class MediaAsset(Resource, BaseMediaAsset):

    implements(IMediaAsset)

    proxyInterface = IMediaAssetView

    def __init__(self, title=u''):
        super(MediaAsset, self).__init__()
        self.title = title

    def _setData(self, data):
        dataFile = StringIO(data)  # let File tear it into pieces
        super(MediaAsset, self)._setData(dataFile)
        if not self.contentType:
            self.guessContentType(data)

    data = property(BaseMediaAsset._getData, _setData)

    def guessContentType(self, data):
        if not isinstance(data, str): # seems to be a file object
            data = data.read(20)
        if data.startswith('%PDF'):
            self.contentType = 'application/pdf'


class ResourceManager(BTreeContainer):

    implements(IResourceManager, ILoopsContained)

    def getLoopsRoot(self):
        return zapi.getParent(self)

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()


class DocumentWriteFileAdapter(object):

    implements(IWriteFile)
    adapts(IDocument)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        self.context.data = unicode(data.replace('\r', ''), 'UTF-8')


class DocumentReadFileAdapter(object):

    implements(IReadFile)
    adapts(IDocument)

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
        return ' '.join((zapi.getName(context), context.title, context.data)).strip()

    def title(self):
        context = self.context
        return ' '.join((zapi.getName(context), context.title,)).strip()


class IndexableResource(object):

    implements(IIndexableContent)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def indexableContent(self, fields):
        context = self.context
        icc = IndexContentCollector()
        icc.addBinary(fields[0], context.data, context.contentType, language='de')
        return icc

