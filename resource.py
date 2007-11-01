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
from zope.app.security.interfaces import IAuthentication
from zope.filerepresentation.interfaces import IReadFile, IWriteFile
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.dublincore.interfaces import IZopeDublinCore
from zope.filerepresentation.interfaces import IFileFactory
from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from zope.size.interfaces import ISized
from zope.security.proxy import removeSecurityProxy
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
from cybertools.util.jeep import Jeep

from loops.base import ParentInfo
from loops.common import ResourceAdapterBase, adapted
from loops.concept import ResourceRelation
from loops.interfaces import IBaseResource, IResource
from loops.interfaces import IFile, IExternalFile, INote
from loops.interfaces import IDocument, ITextDocument, IDocumentSchema, IDocumentView
from loops.interfaces import IMediaAsset, IMediaAssetView
from loops.interfaces import IResourceManager, IResourceManagerContained
from loops.interfaces import ITypeConcept
from loops.interfaces import ILoopsContained
from loops.interfaces import IIndexAttributes
from loops import util
from loops.versioning.util import getMaster
from loops.view import TargetRelation

_ = MessageFactory('loops')


class ResourceManager(BTreeContainer):

    implements(IResourceManager, ILoopsContained)

    def getLoopsRoot(self):
        return zapi.getParent(self)

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()

    def getAllParents(self, collectGrants=False):
        return Jeep()


class Resource(Image, Contained):

    # TODO: remove dependency on Image

    implements(IBaseResource, IResource, IResourceManagerContained,
               IRelatable, ISized)

    proxyInterface = IMediaAssetView  # obsolete!

    storageName = None

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
        if concept is None: # this should not happen
            return
        current = self.getResourceType()
        if current != concept:
            # change storage if necessary, and migrate data
            oldType = IType(self)
            from loops.type import ConceptTypeInfo
            newType = ConceptTypeInfo(concept)
            self.migrateStorage(oldType, newType)
            # assign new type parent
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
        #if not data:
        #    return
        dataFile = StringIO(data)  # let File tear it into pieces
        super(Resource, self)._setData(dataFile)
        if not self.contentType:
            self.guessContentType(data)
        self._size = len(data)
    data = property(Image._getData, _setData)

    def guessContentType(self, data):
        # probably obsolete, use zope.contenttype.guess_content_type()
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

    def getAllParents(self, collectGrants=False):
        result = Jeep()
        for rel in self.getConceptRelations():
            obj = rel.first
            uid = util.getUidForObject(obj)
            pi = result.setdefault(uid, ParentInfo(obj))
            if rel not in pi.relations:
                pi.relations.append(rel)
            obj.getAllParents(collectGrants, result)
        return result

    # concept relations
    # note: we always use the master version for relations, see getMaster()

    def getClients(self, relationships=None):
        if relationships is None:
            relationships = [TargetRelation]
        obj = getMaster(self)  # use the master version for relations
        rels = getRelations(second=obj, relationships=relationships)
        return [r.first for r in rels]

    def getConceptRelations (self, predicates=None, concept=None):
        predicates = predicates is None and ['*'] or predicates
        obj = getMaster(self)
        relationships = [ResourceRelation(None, obj, p) for p in predicates]
        # TODO: sort...
        return getRelations(first=concept, second=obj, relationships=relationships)

    def getConcepts(self, predicates=None):
        obj = getMaster(self)
        return [r.first for r in obj.getConceptRelations(predicates)]

    def assignConcept(self, concept, predicate=None, order=0, relevance=1.0):
        obj = getMaster(self)
        concept.assignResource(obj, predicate, order, relevance)

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

    # storage migration

    def migrateStorage(self, oldType, newType):
        oldType = removeSecurityProxy(oldType)
        newType = removeSecurityProxy(newType)
        context = removeSecurityProxy(self)
        oldAdapted = newAdapted = context
        oldTi = removeSecurityProxy(oldType.typeInterface)
        if oldTi is not None:
            oldAdapted = oldTi(context, None)
        if oldAdapted is None: # nothing to migrate
            return
        newTi = removeSecurityProxy(newType.typeInterface)
        newOptions = {}
        if newTi is not None:
            newAdapted = newTi(context, None)
            if newAdapted is not None:
                # make sure we use options of new type:
                newOptions = newType.optionsDict
                object.__setattr__(newAdapted, 'options', newOptions)
        #print 'migrateStorage:', newAdapted, newOptions, oldAdapted, oldAdapted.storageName
        if newAdapted is not None and newOptions.get('storage') != oldAdapted.storageName:
            data = oldAdapted.data
            #print 'data', data
            oldAdapted.data = ''            # clear old storage
            context._storageName = None     # let's take storage from new type options
            context._storageParams = None   # "
            newAdapted.data = data


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

    externalAddress = None

    def setData(self, data):
        #if self.storageName is None:
        #    self.storageName = 'zopefile'
        self.storageName = None
        self.context.data = data
    def getData(self): return self.context.data
    data = property(getData, setData)

    @Lazy
    def options(self):
        return IType(self.context).optionsDict

    def getStorageName(self):
        return (getattr(self.context, '_storageName', None)
             or self.options.get('storage', None))
    def setStorageName(self, value):
        self.context._storageName = value
    storageName = property(getStorageName, setStorageName)


class ExternalFileAdapter(FileAdapter):

    implements(IExternalFile)

    _adapterAttributes = (FileAdapter._adapterAttributes
                       + ('storageParams', 'externalAddress', 'uniqueAddress'))

    def getStorageParams(self):
        params = getattr(self.context, '_storageParams', None)
        if params is not None:
            return params
        else:
            value = self.options.get('storage_parameters') or 'extfiles'
            return dict(subdirectory=value)
    def setStorageParams(self, value):
        self.context._storageParams = value
    storageParams = property(getStorageParams, setStorageParams)

    def getExternalAddress(self):
        return getattr(self.context, '_externalAddress', self.context.__name__)
    def setExternalAddress(self, addr):
        # TODO (?) - use intId as default?
        self.context._externalAddress = addr
    externalAddress = property(getExternalAddress, setExternalAddress)

    @property
    def uniqueAddress(self):
        storageParams = self.storageParams
        storageName = self.storageName
        storage = component.getUtility(IExternalStorage, name=storageName)
        return storage.getUniqueAddress(self.externalAddress, storageParams)

    def setData(self, data):
        storageParams = self.storageParams
        storageName = self.storageName
        storage = component.getUtility(IExternalStorage, name=storageName)
        storage.setData(self.externalAddress, data, params=storageParams)
        self.context._size = len(data)
        # remember storage settings:
        self.storageParams = storageParams
        self.storageName = storageName

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

    implements(ITextDocument)
    _contextAttributes = list(ITextDocument) + list(IBaseResource)


class NoteAdapter(DocumentAdapter):
    """ A note is a short text document with an associated link.
    """

    implements(INote)
    _contextAttributes = list(INote) + list(IBaseResource)

    @property
    def description(self):
        return self.data.replace('\n', ' ')


# other adapters

class DocumentWriteFileAdapter(object):

    implements(IWriteFile)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        #ti = IType(self.context).typeInterface
        #context = ti is None and self.context or ti(self.context)
        context = adapted(self.context)
        if ITextDocument.providedBy(context) or IDocument.providedBy(context):
            context.data = unicode(data.replace('\r', ''), 'UTF-8')
        else:
            # don't decode files or external files even if contentType == 'text/...'
            # TODO: make use of tmpfile when using external files
            context.data = data
        notify(ObjectModifiedEvent(self.context, Attributes(IResource, 'data')))


class DocumentReadFileAdapter(object):

    implements(IReadFile)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    @Lazy
    def data(self):
        return adapted(self.context).data

    def read(self):
        data = self.data
        if type(data) is unicode:
            return self.data.encode('UTF-8')
        else:
            return data

    def size(self):
        return len(self.data)


class ExternalFileFactory(object):

    implements(IFileFactory)
    adapts(IResourceManager)

    def __init__(self, context):
        self.context = removeSecurityProxy(context)

    def __call__(self, name, contentType, data):
        res = Resource()
        self.context[name] = res  # to be able to set resourceType
        cm = self.context.getLoopsRoot().getConceptManager()
        res.resourceType = cm['extfile']
        obj = adapted(res)
        obj.contentType = contentType
        obj.data = data
        notify(ObjectModifiedEvent(res))
        del self.context[name]  # will be set again by put
        return res


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
        return ' '.join([getName(context),
                         context.title, context.description] +
                        self.creators()).strip()

    def creators(self):
        cr = IZopeDublinCore(self.context).creators or []
        pau = component.getUtility(IAuthentication)
        creators = []
        for c in cr:
            principal = pau.getPrincipal(c)
            if principal is not None:
                creators.append(principal.title)
        return creators


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

