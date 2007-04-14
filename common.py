#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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

from zope.app.container.contained import NameChooser as BaseNameChooser
from zope.dublincore.interfaces import IZopeDublinCore
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.dublincore.zopedublincore import ScalarProperty
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy

from cybertools.storage.interfaces import IStorageInfo
from loops.interfaces import ILoopsObject, ILoopsContained, IConcept, IResource
from loops.interfaces import IResourceAdapter


# type interface adapters

class AdapterBase(object):
    """ (Mix-in) Class for concept adapters that provide editing of fields
        defined by the type interface.
    """

    adapts(IConcept)

    _adapterAttributes = ('context', '__parent__', )
    _contextAttributes = list(IConcept)

    def __init__(self, context):
        self.context = context
        self.__parent__ = context # to get the permission stuff right

    def __getattr__(self, attr):
        self.checkAttr(attr)
        return getattr(self.context, '_' + attr, None)

    def __setattr__(self, attr, value):
        if attr in self._adapterAttributes:
            object.__setattr__(self, attr, value)
        else:
            self.checkAttr(attr)
            setattr(self.context, '_' + attr, value)

    def checkAttr(self, attr):
        if attr not in self._contextAttributes:
            raise AttributeError(attr)

    def __eq__(self, other):
        if other is None:
            return False
        return self.context == other.context


class ResourceAdapterBase(AdapterBase):

    implements(IStorageInfo)
    adapts(IResource)

    _adapterAttributes = ('storageName', 'storageParams', ) + AdapterBase._adapterAttributes
    _contextAttributes = list(IResourceAdapter)

    storageName = None
    storageParams = None


# other adapters

class LoopsDCAdapter(ZDCAnnotatableAdapter):

    implements(IZopeDublinCore)
    adapts(ILoopsObject)

    def __init__(self, context):
        self.context = context
        super(LoopsDCAdapter, self).__init__(context)

    def Title(self):
        return super(LoopsDCAdapter, self).title or self.context.title
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
