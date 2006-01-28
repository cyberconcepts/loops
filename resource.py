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
from zope.interface import implements
from persistent import Persistent
from cStringIO import StringIO
from cybertools.relation.registry import getRelations

from interfaces import IResource
from interfaces import IDocument, IDocumentSchema, IDocumentView
from interfaces import IMediaAsset, IMediaAssetSchema, IMediaAssetView
from interfaces import IResourceManager, IResourceManagerContained
from interfaces import ILoopsContained


class Resource(Contained, Persistent):

    implements(IResource, IResourceManagerContained)

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

    def getLoopsRoot(self):
        return zapi.getParent(self).getLoopsRoot()

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()

    def getClients(self, relationships=None):
        rels = getRelations(second=self, relationships=relationships)
        return [r.first for r in rels]

    def __init__(self, title=u''):
        self.title = title

    _size = _width = _height = 0


class Document(Resource):

    implements(IDocument)

    proxyInterface = IDocumentView

    _data = u''
    def setData(self, data): self._data = data
    def getData(self): return self._data
    data = property(getData, setData)


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



