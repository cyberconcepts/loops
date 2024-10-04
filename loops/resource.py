# loops.resource

""" Definition of the Concept class.
"""

from io import BytesIO
from logging import getLogger
from persistent import Persistent
from zope import component, schema
from zope.app.file.image import Image
from zope.authentication.interfaces import IAuthentication
from zope.container.btree import BTreeContainer
from zope.container.contained import Contained
from zope.contenttype import guess_content_type
from zope.filerepresentation.interfaces import IReadFile, IWriteFile
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.dublincore.interfaces import IZopeDublinCore
from zope.filerepresentation.interfaces import IFileFactory
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.size.interfaces import ISized
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName, getParent
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
from loops.security.common import canListObject
from loops import util
from loops.versioning.util import getMaster
from loops.view import TargetRelation

logger = getLogger('loops.resource')

_ = MessageFactory('loops')


@implementer(IResourceManager, ILoopsContained)
class ResourceManager(BTreeContainer):

    def getLoopsRoot(self):
        return getParent(self)

    def getConceptManager(self):
        return self.getLoopsRoot().getConceptManager()

    def getViewManager(self):
        return self.getLoopsRoot().getViewManager()

    def getAllParents(self, collectGrants=False):
        return Jeep()


@implementer(IBaseResource, IResource, IResourceManagerContained, IRelatable, ISized)
class Resource(Image, Contained):

    # TODO: remove dependency on Image

    proxyInterface = IMediaAssetView  # obsolete!

    storageName = None

    metaInfo = u''

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
        concepts = self.getConcepts([typePred], noSecurityCheck=True)
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

    def setType(self, value):
        self.resourceType = value

    def _setData(self, data):
        dataFile = BytesIO(data)  # let File tear it into pieces
        super(Resource, self)._setData(dataFile)
        if not self.contentType:
            self.guessContentType(data)
        self._size = len(data)
    data = property(Image._getData, _setData)

    def guessContentType(self, data):
        # probably obsolete, use zope.contenttype.guess_content_type()
        if not isinstance(data, (bytes, str)): # seems to be a file object
            data = data.read(20)
        if data.startswith(b'%PDF'):
            self.contentType = 'application/pdf'

    _contentType = u''
    def setContentType(self, contentType):
        if contentType:
            self._contentType = contentType
    def getContentType(self): return self._contentType
    contentType = property(getContentType, setContentType)

    def getLoopsRoot(self):
        return getParent(self).getLoopsRoot()

    def getConceptManager(self):
        return self.getLoopsRoot().getConceptManager()

    @property
    def favTitle(self):
        return self.title

    def getAllParents(self, collectGrants=False, ignoreTypes=False):
        result = Jeep()
        for rel in self.getConceptRelations():
            if (ignoreTypes and
                    rel.predicate == self.getConceptManager().getTypePredicate()):
                continue
            obj = rel.first
            uid = util.getUidForObject(obj)
            pi = result.setdefault(uid, ParentInfo(obj))
            if rel not in pi.relations:
                pi.relations.append(rel)
            obj.getAllParents(collectGrants, result, ignoreTypes)
        return result

    # concept relations
    # note: we always use the master version for relations, see getMaster()

    def getClients(self, relationships=None):
        if relationships is None:
            relationships = [TargetRelation]
        obj = getMaster(self)  # use the master version for relations
        rels = getRelations(second=obj, relationships=relationships)
        return [r.first for r in rels if canListObject(r.first)]

    def getConceptRelations (self, predicates=None, concept=None, sort='default',
                             noSecurityCheck=False, usePredicateIndex=False):
        predicates = predicates is None and ['r*'] or predicates
        obj = getMaster(self)
        relationships = [ResourceRelation(None, obj, p) for p in predicates]
        if sort == 'default':
            #sort = lambda x: (x.order, x.first.title.lower())
            sort = lambda x: (x.first.title.lower())
        rels = (r for r in getRelations(first=concept, second=obj,
                                        relationships=relationships,
                                        usePredicateIndex=usePredicateIndex)
                  if canListObject(r.first, noSecurityCheck))
        return sorted(rels, key=sort)

    def getConcepts(self, predicates=None, noSecurityCheck=False, 
                    usePredicateIndex=False):
        obj = getMaster(self)
        return [r.first for r in obj.getConceptRelations(predicates,
                                    noSecurityCheck=noSecurityCheck,
                                    usePredicateIndex=usePredicateIndex)]

    # simplify common access for concepts and resources:
    getParentRelations = getConceptRelations
    getParents = getConcepts

    def assignConcept(self, concept, predicate=None, order=0, relevance=1.0):
        obj = getMaster(self)
        concept.assignResource(obj, predicate, order, relevance)

    def deassignConcept(self, concept, predicates=None):
        obj = getMaster(self)
        concept.deassignResource(obj, predicates)

    def assignParent(self, concept, predicate=None, order=0, relevance=1.0):
        self.assignConcept(concept, predicate=predicate, order=order,
                           relevance=relevance)

    def deassignParent(self, parent, predicates=None, noSecurityCheck=False):
        self.deassignConcept(parent, predicates=predicates)

    # ISized interface
    def getSize(self):
        if self._size:
            return self._size
        adobj = adapted(self)
        size = getattr(adobj, 'size', None)
        if size is None:
            return len(adobj.data)
        return size

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
            oldAdapted.data = b''            # clear old storage
            context._storageName = None     # let's take storage from new type options
            context._storageParams = None   # "
            if data:    # do not write empty files
                newAdapted.data = data


# Document and MediaAsset are legacy classes, will become obsolete

@implementer(IDocument)
class Document(Resource):

    proxyInterface = IDocumentView

    def __init__(self, title=u''):
        self.title = title

    _data = u''
    def setData(self, data):
        self._data = data.replace('\r', '')
        self._size = len(data)
    def getData(self):
        return self._data
    data = property(getData, setData)


@implementer(IMediaAsset)
class MediaAsset(Resource):

    pass


# type adapters

@implementer(IFile)
class FileAdapter(ResourceAdapterBase):
    """ A type adapter for providing file functionality for resources.
    """

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


@implementer(IExternalFile)
class ExternalFileAdapter(FileAdapter):

    _adapterAttributes = (FileAdapter._adapterAttributes
                        + ('storageParams', 'externalAddress', 'uniqueAddress',
                           'processingErrors'))

    processingErrors = []

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
        return getattr(self.context, '_externalAddress', None) or self.context.__name__
    def setExternalAddress(self, addr):
        self.context._externalAddress = addr
        if addr:
            data = self.data
            self.context._size = len(data)
            contentType = guess_content_type(addr, self.data[:100])
            if contentType:
                self.contentType = contentType[0]
    externalAddress = property(getExternalAddress, setExternalAddress)

    localFilename = externalAddress

    @property
    def uniqueAddress(self):
        storageParams = self.storageParams
        storageName = self.storageName
        storage = component.getUtility(IExternalStorage, name=storageName)
        return storage.getUniqueAddress(self.externalAddress, storageParams)

    def setData(self, data):
        storageParams = self.storageParams
        storageName = self.storageName
        externalAddress = self.externalAddress
        storage = component.getUtility(IExternalStorage, name=storageName)
        storage.setData(self.externalAddress, data, params=storageParams)
        self.context._size = len(data)
        # remember storage settings:
        self.storageParams = storageParams
        self.storageName = storageName
        self.externalAddress = externalAddress

    def getData(self):
        if self.storageName in ('unknown', None):    # object not set up yet
            return ''
        return self.storage.getData(self.externalAddress, params=self.storageParams)

    data = property(getData, setData)

    @property
    def size(self):
        if self.storageName in ('unknown', None):    # object not set up yet
            return ''
        return self.storage.getSize(self.externalAddress, params=self.storageParams)

    @Lazy
    def storage(self):
        return component.getUtility(IExternalStorage, name=self.storageName)

    @Lazy
    def modified(self):
        return self.storage.getMTime(self.externalAddress, self.storageParams)

    def copyDataFile(self, targetParams, targetAddress=None):
        storageParams = self.storageParams
        externalAddress = self.externalAddress
        self.storage.copyDataFile(self.externalAddress, self.storageParams,
                                  targetAddress or self.externalAddress,
                                  targetParams)

class DocumentAdapter(ResourceAdapterBase):
    """ Common base class for all resource types with a text-like
        data attribute.
    """

    # let the adapter handle the data attribute:
    _adapterAttributes = ResourceAdapterBase._adapterAttributes + ('data',)

    def setData(self, data):
        if isinstance(data, bytes):
            data = data.decode('UTF-8')
        self.context._data = data.replace('\r', '')
        self.context._size = len(data)
    def getData(self): return self.context._data
    data = property(getData, setData)


@implementer(ITextDocument)
class TextDocumentAdapter(DocumentAdapter):
    """ A type adapter for providing text document functionality for resources.
    """

    _contextAttributes = list(ITextDocument) + list(IBaseResource)


@implementer(INote)
class NoteAdapter(DocumentAdapter):
    """ A note is a short text document with an associated link.
    """

    _contextAttributes = list(INote) + list(IBaseResource)

    @property
    def description(self):
        return self.data.replace('\n', ' ')


# other adapters

@implementer(IWriteFile)
class DocumentWriteFileAdapter(object):

    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        #ti = IType(self.context).typeInterface
        #context = ti is None and self.context or ti(self.context)
        context = adapted(self.context)
        if ITextDocument.providedBy(context) or IDocument.providedBy(context):
            #context.data = unicode(data.replace('\r', ''), 'UTF-8')
            context.data = util.toUnicode(data.replace('\r', ''))
        else:
            # don't decode files or external files even if contentType == 'text/...'
            # TODO: make use of tmpfile when using external files
            context.data = data
        notify(ObjectModifiedEvent(self.context, Attributes(IResource, 'data')))


@implementer(IReadFile)
class DocumentReadFileAdapter(object):

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


@implementer(IFileFactory)
class ExternalFileFactory(object):

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


@implementer(IIndexAttributes)
class IndexAttributes(object):

    adapts(IResource)

    def __init__(self, context):
        self.context = context

    @Lazy
    def adapted(self):
        return adapted(self.context)

    @Lazy
    def adaptedIndexAttributes(self):
        #if self.adapted != self.context:
        if isinstance(self.adapted, ResourceAdapterBase):
            #return component.queryAdapter(self.adapted, IIndexAttributes)
            return IIndexAttributes(self.adapted, None)

    def text(self):
        actx = adapted(self.context)
        txt = transformToText(actx)
        if txt is not None:
            return txt
        if not actx.contentType.startswith('text'):
            return u''
        data = actx.data
        if type(data) != str:
            try:
                data = data.decode('UTF-8')
            except UnicodeDecodeError:
                data = data.decode('ISO8859-15')
        return data

    def xx_text(self):
        context = self.context
        ti = IType(context).typeInterface
        if ti is not None:
            adapted = ti(context)
            transform = component.queryAdapter(adapted, ITextTransform,
                                               name=context.contentType)
            if transform is not None:
                rfa = component.queryAdapter(IReadFile, adapted)
                if rfa is None:
                    data = transform(BytesOP(adapted.data))
                    return data
                else:
                    return transform(rfa)
        if not context.contentType.startswith('text'):
            return u''
        data = context.data
        if type(data) != str:
            data = data.decode('UTF-8')
        return data

    def title(self):
        context = self.context
        return ' '.join([getName(context),
                         context.title, context.description] +
                        self.creators()).strip()

    def creators(self):
        from loops.organize.util import getPrincipalForUserId
        cr = IZopeDublinCore(self.context).creators or []
        pau = component.getUtility(IAuthentication, context=self.context)
        creators = []
        for c in cr:
            principal = getPrincipalForUserId(c, auth=pau)
            if principal is None:
                creators.append(c)
            else:
                creators.append(principal.title)
        return creators

    def identifier(self):
        return getName(self.context)

    def keywords(self):
        if self.adaptedIndexAttributes is not None:
            return self.adaptedIndexAttributes.keywords()


def transformToText(obj, data=None, contentType=None):
    if data is None:
        data = obj.data
    if contentType is None:
        contentType = obj.contentType
    transform = component.queryAdapter(obj, ITextTransform, name=contentType)
    if transform is not None:
        #rfa = component.queryAdapter(IReadFile, obj)
        rfa = IReadFile(obj, None)
        if rfa is None:
            if isinstance(data, str):
                data = data.encode('UTF-8')
            try:
                return transform(BytesIO(data))
            except:
                import traceback
                logger.warn(traceback.format_exc())
                return u''
        else:
            return transform(rfa)


@implementer(schema.interfaces.IIterableSource)
class ResourceTypeSourceList(object):

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
