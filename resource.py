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

from zope import component, schema
from zope.app import zapi
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained
from zope.app.file.image import Image
from zope.app.file.interfaces import IFile
from zope.filerepresentation.interfaces import IReadFile, IWriteFile
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from zope.size.interfaces import ISized
from zope.traversing.api import getName, getParent
from persistent import Persistent
from cStringIO import StringIO

from zope.lifecycleevent import ObjectModifiedEvent, Attributes
from zope.event import notify

from cybertools.relation.registry import getRelations
from cybertools.relation.interfaces import IRelatable
from cybertools.storage.interfaces import IExternalStorage
from cybertools.text.interfaces import ITextTransform
from cybertools.typology.interfaces import IType, ITypeManager

from loops.interfaces import IBaseResource, IResource
from loops.interfaces import IFile, IExternalFile, INote
from loops.interfaces import IDocument, ITextDocument, IDocumentSchema, IDocumentView
from loops.interfaces import IMediaAsset, IMediaAssetView
from loops.interfaces import IResourceManager, IResourceManagerContained
from loops.interfaces import ILoopsContained
from loops.interfaces import IIndexAttributes
from loops.concept import ResourceRelation
from loops.common import ResourceAdapterBase
from loops.versioning.util import getMaster
from loops.view import TargetRelation

_ = MessageFactory('loops')


class ResourceManager(BTreeContainer):

    implements(IResourceManager, ILoopsContained)

    def getLoopsRoot(self):
        return zapi.getParent(self)

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()


class Resource(Image, Contained):

    # TODO: remove dependency on Image

    implements(IBaseResource, IResource, IResourceManagerContained, IRelatable, ISized)

    proxyInterface = IMediaAssetView  # obsolete!

    _size = _width = _height = 0

    def __init__(self, title=u''):
        super(Resource, self).__init__()
        self.title = title

    _title = u''
    def getTitle(self): return self._title
    def setTitle(self, title): self._title = title
    title = property(getTitle, setTitle)

    _description = u''
    def getDescription(self): return self._description
    def setDescription(self, description): self._description = description
    description = property(getDescription, setDescription)

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
                raise ValueError('No type predicate found for ' + getName(self))
            if current is not None:
                self.deassignConcept(current, [typePred])
            self.assignConcept(concept, typePred)
    resourceType = property(getResourceType, setResourceType)

    def getType(self):
        return self.resourceType

    def _setData(self, data):
        dataFile = StringIO(data)  # let File tear it into pieces
        super(Resource, self)._setData(dataFile)
        if not self.contentType:
            self.guessContentType(data)
        self._size = len(data)
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
        obj = getMaster(self)  # use the master version for relations
        rels = getRelations(second=obj, relationships=relationships)
        return [r.first for r in rels]

    # concept relations
    # note: we always use the master version for relations, see getMaster()

    def getConceptRelations (self, predicates=None, concept=None):
        predicates = predicates is None and ['*'] or predicates
        obj = getMaster(self)
        relationships = [ResourceRelation(None, obj, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=concept, second=obj, relationships=relationships)

    def getConcepts(self, predicates=None):
        obj = getMaster(self)
        return [r.first for r in obj.getConceptRelations(predicates)]

    def assignConcept(self, concept, predicate=None):
        obj = getMaster(self)
        concept.assignResource(obj, predicate)

    def deassignConcept(self, concept, predicates=None):
        obj = getMaster(self)
        concept.deassignResource(obj, predicates)

    # ISized interface

    def getSize(self):
        if self._size:
            return self._size
        tp = IType(self, None)
        if tp is not None:
            ti = tp.typeInterface
            if ti is not None:
                return len(ti(self).data)
        return len(self.data)

    def sizeForSorting(self):
        return 'byte', self.getSize()

    def sizeForDisplay(self):
        size = self.getSize()
        kb = 1024.0
        unit = 'B'
        if size < kb:
            return '%.0f %s' % (size, unit)
        unit = 'kB'
        size = size / kb
        if size >= kb:
            unit = 'MB'
            size = size / kb
        size = round(size, 1)
        return '%.1f %s' % (size, unit)
        #return '%s %s' % (util.getNiceNumber(size), unit)


# Document and MediaAsset are legacy classes, will become obsolete

class Document(Resource):

    implements(IDocument)

    proxyInterface = IDocumentView

    def __init__(self, title=u''):
        self.title = title

    _data = u''
    def setData(self, data):
        self._data = data.replace('\r', '')
        self._size = len(data)
    def getData(self): return self._data
    data = property(getData, setData)


class MediaAsset(Resource):

    implements(IMediaAsset)


# type adapters

class FileAdapter(ResourceAdapterBase):
    """ A type adapter for providing file functionality for resources.
    """

    implements(IFile)

    _contextAttributes = list(IFile) + list(IBaseResource)
    _adapterAttributes = ResourceAdapterBase._adapterAttributes + ('data',)

    def setData(self, data): self.context.data = data
    def getData(self): return self.context.data
    data = property(getData, setData)


class ExternalFileAdapter(FileAdapter):

    implements(IExternalFile)

    @Lazy
    def externalAddress(self):
        # or is this an editable attribute?
        # or some sort of subpath set during import?
        # anyway: an attribute of the context object.
        return self.context.__name__

    @Lazy
    def options(self):
        return IType(self.context).optionsDict

    @Lazy
    def storageName(self):
        return self.options.get('storage')

    @Lazy
    def storageParams(self):
        params = self.options.get('storage_parameters') or 'extfiles'
        return dict(subdirectory=params)

    def setData(self, data):
        storage = component.getUtility(IExternalStorage, name=self.storageName)
        storage.setData(self.externalAddress, data, params=self.storageParams)
        self.context._size = len(data)

    def getData(self):
        storage = component.getUtility(IExternalStorage, name=self.storageName)
        return storage.getData(self.externalAddress, params=self.storageParams)

    data = property(getData, setData)


class DocumentAdapter(ResourceAdapterBase):
    """ Common base class for all resource types with a text-like
        data attribute.
    """

    # let the adapter handle the data attribute:
    _adapterAttributes = ResourceAdapterBase._adapterAttributes + ('data',)

    def setData(self, data):
        self.context._data = data.replace('\r', '')
        self.context._size = len(data)
    def getData(self): return self.context._data
    data = property(getData, setData)


class TextDocumentAdapter(DocumentAdapter):
    """ A type adapter for providing text document functionality for resources.
    """

    implements(IDocument)
    _contextAttributes = list(IDocument) + list(IBaseResource)


class NoteAdapter(DocumentAdapter):
    """ A note is a short text document with an associated link.
    """

    implements(INote)
    _contextAttributes = list(INote) + list(IBaseResource)


# other adapters

class DocumentWriteFileAdapter(object):

    implements(IWriteFile)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        # TODO: use typeInterface...
        ti = IType(self.context).typeInterface
        context = ti is None and self.context or ti(self.context)
        if ITextDocument.providedBy(context) or IDocument.providedBy(context):
            context.data = unicode(data.replace('\r', ''), 'UTF-8')
        else:
            # TODO: make use of tmpfile when using external files
            context.data = data
        #ITextDocument(self.context).data = unicode(data.replace('\r', ''), 'UTF-8')
        notify(ObjectModifiedEvent(self.context, Attributes(IResource, 'data')))


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
        ti = IType(context).typeInterface
        if ti is not None:
            adapted = ti(context)
            transform = component.queryAdapter(adapted, ITextTransform,
                                               name=context.contentType)
            if transform is not None:
                rfa = component.queryAdapter(IReadFile, adapted)
                if rfa is None:
                    data = transform(StringIO(adapted.data))
                    return data
                else:
                    return transform(rfa)
        if not context.contentType.startswith('text'):
            return u''
        data = context.data
        if type(data) != unicode:
            data = data.decode('UTF-8')
        return data

    def title(self):
        context = self.context
        return ' '.join((getName(context),
                         context.title, context.description)).strip()


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


