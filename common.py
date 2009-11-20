#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Common stuff.

$Id$
"""

from zope import component
from zope.app.container.contained import NameChooser as BaseNameChooser
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.dublincore.interfaces import IZopeDublinCore
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.zopedublincore import ScalarProperty
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.security.proxy import isinstance
from zope.traversing.api import getName

from cybertools.storage.interfaces import IStorageInfo
from cybertools.typology.interfaces import IType
from loops.interfaces import ILoopsObject, ILoopsContained
from loops.interfaces import IConcept, IResource, IResourceAdapter
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
        if isinstance(arg, basestring):
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

    _adapterAttributes = ('context', '__parent__',)
    _contextAttributes = list(IConcept)
    _noexportAttributes = ()
    _textIndexAttributes = ()

    __is_dummy__ = False
    __type__ = None

    languageInfo = None

    def __init__(self, context):
        self.context = context
        self.__parent__ = context # to get the permission stuff right

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
            return False
        return self.context == other.context

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

    def getChildren(self):
        for c in self.context.getChildren():
            yield adapted(c, self.languageInfo)


class ResourceAdapterBase(AdapterBase):

    implements(IStorageInfo)
    adapts(IResource)

    _adapterAttributes = adapterAttributes('storageName', 'storageParams', AdapterBase)
    _contextAttributes = list(IResourceAdapter)

    storageName = None
    storageParams = None
    localFilename = None

    def getChildren(self):
        return []


# other adapters

class LoopsDCAdapter(ZDCAnnotatableAdapter):

    implements(IZopeDublinCore)
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

    def chooseName(self, name, obj):
        if not name:
            name = self.generateNameFromTitle(obj)
        else:
            name = self.normalizeName(name)
        name = super(NameChooser, self).chooseName(name, obj)
        return name

    def generateNameFromTitle(self, obj):
        title = obj.title
        if len(title) > 15:
            words = title.split()
            if len(words) > 1:
                title = '_'.join((words[0], words[-1]))
        return self.normalizeName(title)

    def normalizeName(self, baseName):
        result = []
        for c in baseName:
            try:
                c = c.encode('ISO8859-15')
            except UnicodeEncodeError:
                # skip all characters not representable in ISO encoding
                continue
            if c in '._':
                # separator and special characters to keep
                result.append(c)
                continue
            if c in self.specialCharacters:
                # transform umlauts and other special characters
                result.append(self.specialCharacters[c].lower())
                continue
            if ord(c) > 127:
                # map to ASCII characters
                c = chr(ord(c) & 127)
            if c in ':,/\\ ':
                # replace separator characters with _
                result.append('_')
                # skip all other characters
            elif not c.isalpha() and not c.isdigit():
                continue
            else:
                result.append(c.lower())
        name = unicode(''.join(result))
        return name

    specialCharacters = {
        '\xc4': 'Ae', '\xe4': 'ae', '\xd6': 'Oe', '\xf6': 'oe',
        '\xdc': 'Ue', '\xfc': 'ue', '\xdf': 'ss'}


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

    def __init__(self, context, predicateName, interface=None, noSecurityCheck=False):
        self.adapted = context
        if isinstance(context, AdapterBase):
            self.context = context.context
        else:
            self.context = context
        self.predicateName = predicateName
        self.interface = interface
        self.noSecurityCheck = noSecurityCheck

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def conceptManager(self):
        return self.loopsRoot.getConceptManager()

    @Lazy
    def predicate(self):
        return self.conceptManager[self.predicateName]


class ParentRelationSet(RelationSet):

    def add(self, related, order=0, relevance=1.0):
        if isinstance(related, AdapterBase):
            related = related.context
        self.context.deassignParent(related, [self.predicate],  # avoid duplicates
                                    noSecurityCheck=self.noSecurityCheck)
        self.context.assignParent(related, self.predicate, order, relevance)

    def remove(self, related):
        if isinstance(related, AdapterBase):
            related = related.context
        self.context.deassignParent(related, [self.predicate])

    def __iter__(self):
        if self.adapted.__is_dummy__:
            return
        for c in self.context.getParents([self.predicate],
                                         noSecurityCheck=self.noSecurityCheck):
            a = adapted(c, langInfo=self.langInfo)
            if self.interface is None or self.interface.providedBy(a):
                yield a

    def getRelations(self, check=None, noSecurityCheck=None):
        if self.adapted.__is_dummy__:
            return
        if noSecurityCheck is None:
            noSecurityCheck = self.noSecurityCheck
        for r in self.context.getParentRelations([self.predicate],
                                                 noSecurityCheck=noSecurityCheck):
            if check is None or check(r):
                yield r

    def getRelated(self, check=None, noSecurityCheck=None):
        for r in self.getRelations(check, noSecurityCheck):
            yield adapted(r.first, langInfo=self.langInfo)


class ChildRelationSet(RelationSet):

    def add(self, related, order=0, relevance=1.0):
        if isinstance(related, AdapterBase):
            related = related.context
        self.context.deassignChild(related, [self.predicate])   # avoid duplicates
        self.context.assignChild(related, self.predicate, order, relevance)

    def remove(self, related):
        if isinstance(related, AdapterBase):
            related = related.context
        self.context.deassignChild(related, [self.predicate])

    def __iter__(self):
        if self.adapted.__is_dummy__:
            return
        for c in self.context.getChildren([self.predicate]):
            yield adapted(c, langInfo=self.langInfo)


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

    def __init__(self, predicateName, interface=None, noSecurityCheck=False):
        self.predicateName = predicateName
        self.interface = interface
        self.noSecurityCheck = noSecurityCheck

    def __get__(self, inst, class_=None):
        if inst is None:
            return self
        return self.factory(inst, self.predicateName, self.interface,
                            noSecurityCheck=self.noSecurityCheck)

    def __set__(self, inst, value):
        rs = self.factory(inst, self.predicateName)
        current = list(rs)
        for c in current:
            if c not in value:
                rs.remove(c)
        for v in value:
            if v not in current:
                rs.add(v)


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
        s = ParentRelationSet(inst, self.predicateName)
        for current in s:
            if current != value:
                s.remove(current)
        if value is not None:
            s.add(value)    # how to supply additional parameters?


# caching (TBD)

def cached(obj):
    return obj

