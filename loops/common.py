# loops.common

""" Common stuff.
"""

from zope import component
from zope.app.container.contained import NameChooser as BaseNameChooser
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.dublincore.interfaces import IZopeDublinCore
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.zopedublincore import ScalarProperty
from zope.interface import implementer
from zope.interface.interface import InterfaceClass
from zope.security.proxy import isinstance
from zope.traversing.api import getName

from cybertools.storage.interfaces import IStorageInfo
from cybertools.tracking.interfaces import ITrackingStorage
from cybertools.typology.interfaces import IType
from loops.interfaces import ILoopsObject, ILoopsContained
from loops.interfaces import IConcept, IResource, IResourceAdapter
from loops.interfaces import ITracks
from loops import util


# convenience functions

def adapted(obj, langInfo=None):
    """ Return adapter based on the object type's type interface.
    """
    if isinstance(obj, AdapterBase):
        return obj
    t = IType(obj, None)
    if t is not None:
        ti = t.typeInterface
        if ti is not None:
            adapted = component.queryAdapter(obj, ti)
            from loops.i18n.common import I18NAdapterBase
            if isinstance(adapted, I18NAdapterBase):
                adapted.languageInfo = langInfo
            if adapted is not None:
                return adapted
    return obj

def baseObject(obj):
    if isinstance(obj, AdapterBase):
        return obj.context
    return obj


# helper functions for specifying automatic attribute handling

def collectAttributeNames(lst, name):
    attrs = []
    for arg in lst:
        if isinstance(arg, str):
            attrs.append(arg)
        elif isinstance(arg, type):
            attrs.extend(list(getattr(arg, name)))
        elif isinstance(arg, InterfaceClass):
            attrs.extend(list(arg))
        else:
            raise ValueError("Argument must be string or class, '%s' is '%s'." %
                             (arg, type(arg)))
    return tuple(attrs)

def adapterAttributes(*args):
    return collectAttributeNames(args, '_adapterAttributes')

def contextAttributes(*args):
    return collectAttributeNames(args, '_contextAttributes')


# type interface adapters

class AdapterBase(object):
    """ (Mix-in) Class for concept adapters that provide editing of fields
        defined by the type interface.
    """

    adapts(IConcept)

    _adapterAttributes = ('context', '__parent__', 'request')
    _contextAttributes = list(IConcept)
    _noexportAttributes = ()
    _textIndexAttributes = ()

    __is_dummy__ = False
    __type__ = None

    request = None
    languageInfo = None

    def __init__(self, context):
        self.context = context
        self.__parent__ = context # to get the permission stuff right

    def __hash__(self):
        return hash(self.context)

    def __getattr__(self, attr):
        self.checkAttr(attr)
        return getattr(self.context, '_' + attr, None)

    def __setattr__(self, attr, value):
        if attr.startswith('__') or attr in self._adapterAttributes:
            try:
                object.__setattr__(self, attr, value)
            except AttributeError:
                from logging import getLogger
                getLogger('loops.common.AdapterBase').warn(
                            'AttributeError: %r, %r, %r.' %
                                (self.context.__name__, attr, value))
                raise
        else:
            self.checkAttr(attr)
            setattr(self.context, '_' + attr, value)

    def checkAttr(self, attr):
        if attr not in self._contextAttributes:
            raise AttributeError('%s: %s' % (self, attr))

    def __eq__(self, other):
        if not isinstance(other, AdapterBase):
            return self.context == other
        return self.context == other.context

    def __ne__(self, other):
        if not isinstance(other, AdapterBase):
            return self.context != other
        return self.context != other.context

    @Lazy
    def loopsRoot(self):
        return self.getLoopsRoot()

    def getLoopsRoot(self):
        return self.context.getLoopsRoot()

    @property
    def name(self):
        return getName(self.context)

    @Lazy
    def type(self):
        return self.__type__ or self.getType()

    def getType(self):
        return adapted(self.context.getType())

    @Lazy
    def uid(self):
        return util.getUidForObject(self.context)

    @Lazy
    def favTitle(self):
        return self.title

    def getChildren(self, predicates=None):
        for c in self.context.getChildren(predicates):
            yield adapted(c, self.languageInfo)

    def getLongTitle(self):
        return self.title


@implementer(IStorageInfo)
class ResourceAdapterBase(AdapterBase):

    adapts(IResource)

    _adapterAttributes = adapterAttributes('storageName', 'storageParams', AdapterBase)
    _contextAttributes = list(IResourceAdapter)

    storageName = None
    storageParams = None
    localFilename = None

    def getChildren(self):
        return []


# other adapters

@implementer(IZopeDublinCore)
class LoopsDCAdapter(ZDCAnnotatableAdapter):

    adapts(ILoopsObject)

    languageInfo = None

    def __init__(self, context):
        self.context = context
        super(LoopsDCAdapter, self).__init__(context)

    def Title(self):
        return (super(LoopsDCAdapter, self).title
                    or adapted(self.context, self.languageInfo).title)
    def setTitle(self, value):
        ScalarProperty(u'Title').__set__(self, value)
    title = property(Title, setTitle)


class NameChooser(BaseNameChooser):

    adapts(ILoopsContained)

    prefix = u''

    def chooseName(self, name, obj):
        if not name:
            name = self.generateNameFromTitle(obj)
        else:
            name = self.normalizeName(name)
        name = self.prefix + name
        name = super(NameChooser, self).chooseName(name, obj)
        return name

    def generateNameFromTitle(self, obj):
        return generateNameFromTitle(obj.title)

    def normalizeName(self, baseName):
        return normalizeName(baseName)


def generateNameFromTitle(title):
        if len(title) > 15:
            words = title.split()
            if len(words) > 1:
                title = '_'.join((words[0], words[-1]))
        return normalizeName(title)

def normalizeName(baseName):
    specialCharacters = {
        b'\xc4': 'Ae', b'\xe4': 'ae', b'\xd6': 'Oe', b'\xf6': 'oe',
        b'\xdc': 'Ue', b'\xfc': 'ue', b'\xdf': 'ss'}
    result = []
    for c in baseName:
        try:
            x = c.encode('ISO8859-15')
        except UnicodeEncodeError:
            # replace all characters not representable in ISO encoding
            result.append('_')
            continue
        except UnicodeDecodeError:
            result.append('_')
            continue
        if c in '._-':
            # separator and special characters to keep
            result.append(c)
            continue
        if x in specialCharacters:
            # transform umlauts and other special characters
            result.append(specialCharacters[x].lower())
            continue
        if ord(x) > 127:
            # map to ASCII characters
            c = chr(ord(x) & 127).decode('ISO8859-15')
        if c in ':,/\\ ':
            # replace separator characters with _
            result.append('_')
            # skip all other characters
        elif not c.isalpha() and not c.isdigit():
            continue
        else:
            result.append(c.lower())
    name = ''.join(result)
    return name


# virtual attributes/properties

class TypeInstances(object):
    """ Use objects within a ConceptManager object for a collection attribute.
    """

    langInfo = None

    def __init__(self, context, typeName, idAttr='name', prefix='', container=None):
        self.context = context
        self.typeName = typeName
        self.idAttr = idAttr
        self.prefix = prefix
        if container is None:
            self.container = context
        else:
            self.container = context.getLoopsRoot()[container]

    @Lazy
    def typeConcept(self):
        return self.context.getLoopsRoot().getConceptManager()[self.typeName]

    @Lazy
    def typeToken(self):
        return 'loops:concept:' + self.typeName

    @Lazy
    def typePredicate(self):
        return self.context.getTypePredicate()

    def create(self, id, **kw):
        from loops.concept import Concept
        from loops.setup import addAndConfigureObject
        if self.idAttr != 'name' and self.idAttr not in kw:
            kw[self.idAttr] = id
        c = addAndConfigureObject(self.container, Concept, self.prefix + id,
                    conceptType=self.typeConcept, **kw)
        return adapted(c)

    def remove(self, id):
        obj = self.get(id)
        if obj is None:
            raise KeyError(id)
        else:
            del self.context[getName(obj.context)]

    def get(self, id, default=None, langInfo=None):
        from loops.expert import query
        result = (query.Identifier(id) & query.Type(self.typeToken)).apply()
        for obj in query.getObjects(result):
            return adapted(obj, langInfo=self.langInfo)
        else:
            return default

    def __iter__(self):
        for c in self.typeConcept.getChildren([self.typePredicate]):
            yield adapted(c, langInfo=self.langInfo)


class RelationSet(object):
    """ Use relations of a certain predicate for a collection attribute."""

    langInfo = None

    def __init__(self, context, predicateName, interface=None, 
                 noSecurityCheck=False, usePredicateIndex=False):
        self.adapted = context
        self.context = baseObject(context)
        self.predicateName = predicateName
        self.interface = interface
        self.noSecurityCheck = noSecurityCheck
        self.usePredicateIndex = usePredicateIndex

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def conceptManager(self):
        return self.loopsRoot.getConceptManager()

    @Lazy
    def predicate(self):
        return self.conceptManager.get(self.predicateName)


class ParentRelationSet(RelationSet):

    def add(self, related, order=0, relevance=1.0, attrs={}):
        related = baseObject(related)
        self.context.deassignParent(related, [self.predicate],  # avoid duplicates
                                    noSecurityCheck=self.noSecurityCheck)
        self.context.assignParent(related, self.predicate, order, relevance)

    def remove(self, related):
        self.context.deassignParent(baseObject(related), [self.predicate])

    def __iter__(self):
        if self.adapted.__is_dummy__:
            return
        for c in self.context.getParents([self.predicate],
                                         noSecurityCheck=self.noSecurityCheck,
                                         usePredicateIndex=self.usePredicateIndex):
            a = adapted(c, langInfo=self.langInfo)
            if self.interface is None or self.interface.providedBy(a):
                yield a

    def getRelations(self, check=None, noSecurityCheck=None):
        if self.adapted.__is_dummy__:
            return
        if noSecurityCheck is None:
            noSecurityCheck = self.noSecurityCheck
        for r in self.context.getParentRelations([self.predicate],
                                                 noSecurityCheck=noSecurityCheck,
                                                 usePredicateIndex=self.usePredicateIndex):
            if check is None or check(r):
                yield r

    def getRelated(self, check=None, noSecurityCheck=None):
        for r in self.getRelations(check, noSecurityCheck,
                                   usePredicateIndex=self.usePredicateIndex):
            yield adapted(r.first, langInfo=self.langInfo)


class ChildRelationSet(RelationSet):

    def add(self, related, order=0, relevance=1.0, **attrs):
        related = baseObject(related)
        if not attrs:   # no duplicates when relation has no attributes
            self.context.deassignChild(related, [self.predicate])
        rel = self.context.createChildRelation(
                                related, self.predicate, order, relevance)
        if attrs:
            from loops.predicate import adaptedRelation
            adrel = adaptedRelation(rel)
            for k, v in attrs.items():
                setattr(adrel, k, v)

    def remove(self, related):
        related = baseObject(related)
        self.context.deassignChild(related, [self.predicate])

    def __iter__(self):
        if self.adapted.__is_dummy__:
            return
        for c in self.context.getChildren([self.predicate], 
                                          usePredicateIndex=self.usePredicateIndex):
            yield adapted(c, langInfo=self.langInfo)

    def getRelations(self, check=None, noSecurityCheck=None):
        if self.adapted.__is_dummy__:
            return
        if noSecurityCheck is None:
            noSecurityCheck = self.noSecurityCheck
        for r in self.context.getChildRelations([self.predicate],
                                                 noSecurityCheck=noSecurityCheck,
                                                 usePredicateIndex=self.usePredicateIndex):
            if check is None or check(r):
                yield r


# property descriptors

class TypeInstancesProperty(object):

    def __init__(self, typeName, idAttr='name', prefix='', container=None):
        self.typeName = typeName
        self.idAttr = idAttr
        self.prefix = prefix
        self.container = container

    def __get__(self, inst, class_=None):
        if inst is None:
            return self
        return TypeInstances(inst.context, self.typeName, self.idAttr,
                             self.prefix, self.container)


class RelationSetProperty(object):

    def __init__(self, predicateName, interface=None, 
                 noSecurityCheck=False, usePredicateIndex=False):
        self.predicateName = predicateName
        self.interface = interface
        self.noSecurityCheck = noSecurityCheck
        self.usePredicateIndex = usePredicateIndex

    def __get__(self, inst, class_=None):
        if inst is None:
            return self
        return self.factory(inst, self.predicateName, self.interface,
                            noSecurityCheck=self.noSecurityCheck,
                            usePredicateIndex=self.usePredicateIndex)

    def __set__(self, inst, value):
        objects = []
        attrs = []
        hasAttrs = False
        for c in value:
            if isinstance(c, dict):
                objects.append(baseObject(c.pop('object')))
                attrs.append(c)
                hasAttrs = True
            else:
                objects.append(baseObject(c))
                attrs.append({})
        rs = self.factory(inst, self.predicateName)
        current = [baseObject(c) for c in rs]
        for c in current:
            if hasAttrs or c not in objects:
                rs.remove(c)
        for idx, v in enumerate(objects):
            if hasAttrs or v not in current:
                rs.add(v, **attrs[idx])


class ParentRelationSetProperty(RelationSetProperty):

    factory = ParentRelationSet


class ChildRelationSetProperty(RelationSetProperty):

    factory = ChildRelationSet


class ParentRelation(object):
    # TODO: provide special method for supplying relevance and order

    langInfo = None

    def __init__(self, predicateName):
        self.predicateName = predicateName

    def __get__(self, inst, class_=None):
        if inst is None:
            return self
        for obj in ParentRelationSet(inst, self.predicateName):
            return adapted(obj, langInfo=self.langInfo)
        return None

    def __set__(self, inst, value):
        value = baseObject(value)
        rs = ParentRelationSet(inst, self.predicateName)
        rsList = [baseObject(p) for p in rs]
        for current in rsList:
            if current != value:
                rs.remove(current)
        if value is not None:
            if value not in rsList:
                rs.add(value)    # how to supply additional parameters?


# records/tracks

@implementer(ITracks)
class Tracks(object):
    """ A tracking storage adapter managing tracks/records.
    """

    adapts(ITrackingStorage)

    def __init__(self, context):
        self.context = context

    def __getitem__(self, key):
        return self.context[key]

    def __iter__(self):
        return iter(self.context.values())

    def query(self, **criteria):
        if 'task' in criteria:
            criteria['taskId'] = criteria.pop('task')
        if 'party' in criteria:
            criteria['userName'] = criteria.pop('party')
        if 'run' in criteria:
            criteria['runId'] = criteria.pop('run')
        return self.context.query(**criteria)

    def add(self, task, userName, run=0, **kw):
        if not run:
            run = self.context.startRun()
        trackId = self.context.saveUserTrack(task, run, userName, {})
        track = self[trackId]
        track.setData(**kw)
        return track


# caching (TBD)

def cached(obj):
    return obj

