# -*- coding: UTF-8 -*-
# -*- Mode: Python; py-indent-offset: 4 -*-
#
#  Copyright (c) 2019 Helmut Merz helmutm@cy55.de
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
The loops container class.
"""

from zope.app.container.btree import BTreeContainer
from zope.app.folder.folder import Folder
from zope.app.folder.interfaces import IFolder
from zope.traversing.api import getPath, traverse
from zope.interface import implements

from cybertools.util.jeep import Jeep
from loops.interfaces import ILoops

loopsPrefix = '.loops'


class Loops(Folder):
#class Loops(BTreeContainer):

    implements(ILoops)

    #def getSiteManager(self):
    #    return self.__parent__.getSiteManager()

    #@property
    #def _SampleContainer__data(self):
    #    return self.data

    _skinName = ''
    def getSkinName(self): return self._skinName
    def setSkinName(self, skinName): self._skinName = skinName
    skinName = property(getSkinName, setSkinName)

    def getOptions(self): return getattr(self, '_options', [])
    def setOptions(self, value): self._options = value
    options = property(getOptions, setOptions)

    def getLoopsRoot(self):
        return self

    def getAllParents(self, collectGrants=False, ignoreTypes=False):
        return Jeep()

    def getConceptManager(self):
        return self['concepts']

    def getResourceManager(self):
        return self['resources']

    def getViewManager(self):
        return self['views']

    def getRecordManager(self):
        return self.get('records')

    def getLoopsUri(self, obj):
        #return str(loopsPrefix + getPath(obj)[len(getPath(self)):])
        uri = loopsPrefix + getPath(obj)[len(getPath(self)):]
        #if isinstance(uri, unicode):
        #    uri = uri.encode('UTF-8')
        return uri

    def loopsTraverse(self, uri):
        prefix = loopsPrefix + '/'
        if uri.startswith(prefix):
            return traverse(self, uri[len(prefix):])


class ParentInfo(object):

    def __init__(self, obj, relations=None, grants=None):
        self.object = obj
        self.relations = relations or []
        self.grants = grants or []


# backward compatibility for old loops sites that got their Loops object
# directly from loops/__init__.py
import loops
loops.Loops = Loops

