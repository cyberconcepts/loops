# -*- coding: UTF-8 -*-
# -*- Mode: Python; py-indent-offset: 4 -*-
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

$Id$
"""

from zope.app.container.btree import BTreeContainer
from zope.app.folder.folder import Folder
from zope.app.folder.interfaces import IFolder
from zope.traversing.api import getPath, traverse
from zope.interface import implements

from loops.interfaces import ILoops

loopsPrefix = '.loops'


class Loops(Folder):
#class Loops(BTreeContainer):

    implements(ILoops)

    def getSiteManager(self):
        return self.__parent__.getSiteManager()

    @property
    def _SampleContainer__data(self):
        return self.data

    _skinName = ''
    def getSkinName(self): return self._skinName
    def setSkinName(self, skinName): self._skinName = skinName
    skinName = property(getSkinName, setSkinName)

    def getLoopsRoot(self):
        return self

    def getConceptManager(self):
        return self['concepts']

    def getResourceManager(self):
        return self['resources']

    def getViewManager(self):
        return self['views']

    def getLoopsUri(self, obj):
        return str(loopsPrefix + getPath(obj)[len(getPath(self)):])

    def loopsTraverse(self, uri):
        prefix = loopsPrefix + '/'
        if uri.startswith(prefix):
            return traverse(self, uri[len(prefix):])
