#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
Media asset file adapter.

Original authors: Johann Schimpf, Erich Seifert.

$Id$
"""

from datetime import datetime
from logging import getLogger
import os

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.interface import implements

from cybertools.media.asset import MediaAssetFile
from cybertools.storage.interfaces import IExternalStorage
from loops.media.interfaces import IMediaAsset
from loops.resource import ExternalFileAdapter
from loops.type import TypeInterfaceSourceList

transformPrefix = 'asset_transform.'

TypeInterfaceSourceList.typeInterfaces += (IMediaAsset,)


class MediaAsset(MediaAssetFile, ExternalFileAdapter):
    """ Concept adapter for extracting metadata from assets and for creating
        transformation variants.
    """

    implements(IMediaAsset)

    _adapterAttributes = ExternalFileAdapter._adapterAttributes + ('modified',)

    isMediaAsset = True

    def __init__(self, context):
        ExternalFileAdapter.__init__(self, context)

    @Lazy
    def rules(self):
        result = {}
        for key, value in self.options.items():
            if key.startswith(transformPrefix):
                variant = key[len(transformPrefix):]
                result[variant] = value
        return result

    def setData(self, data):
        ExternalFileAdapter.setData(self, data)
        if data and self.getMimeType().startswith('image/'):
            self.transform(self.rules)
    data = property(ExternalFileAdapter.getData, setData)

    def setExternalAddress(self, addr):
        ExternalFileAdapter.setExternalAddress(self, addr)
        if addr and self.getMimeType().startswith('image/'):
            self.transform(self.rules)
    externalAddress = property(ExternalFileAdapter.getExternalAddress,
                               setExternalAddress)

    def getMimeType(self):
        return self.context.contentType or ''

    def getDataPath(self):
        storage = component.getUtility(IExternalStorage, name=self.storageName)
        #print '***', self.storageName, self.storageParams, self.options
        return storage.getDir(self.externalAddress,
                              self.storageParams['subdirectory'])

    def getOriginalData(self):
        return ExternalFileAdapter.getData(self)

    def getModified(self):
        d = getattr(self.context, '_modified', None)
        if not d:
            return datetime.fromtimestamp(os.path.getmtime(self.getDataPath()))
        return d
    def setModified(self, value):
        self.context._modified = value
    modified = property(getModified, setModified)

