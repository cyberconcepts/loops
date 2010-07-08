#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
Resource adapter(s) for MS Office files.

$Id$
"""

from xml.dom.minidom import parseString
from zipfile import ZipFile
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.interface import implements
from zope.traversing.api import getName, getParent

from cybertools.storage.interfaces import IExternalStorage
from loops.common import AdapterBase, adapted
from loops.integrator.interfaces import IOfficeFile
from loops.interfaces import IResource, IExternalFile
from loops.resource import ExternalFileAdapter
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IOfficeFile,)


class OfficeFile(ExternalFileAdapter):
    """ An external file that references a MS Office (2007/2010) file.
        It provides access to the document content and properties.
    """

    implements(IOfficeFile)

    propertyMap = dict(version=u'Revision:')

    def setExternalAddress(self, addr):
        super(OfficeFile, self).setExternalAddress(addr)
        self.processDocument()
    externalAddress = property(ExternalFileAdapter.getExternalAddress,
                               setExternalAddress)

    def processDocument(self):
        storage = component.getUtility(IExternalStorage, name=self.storageName)
        subDir = self.storageParams.get('subdirectory')
        fn = storage.getDir(self.externalAddress, subDir)
        # open ZIP file, process properties, set version property in file
        zf = ZipFile(fn, 'a')
        #print '***', zf.namelist()
        propsXml = zf.read('docProps/custom.xml')
        dom = parseString(propsXml)
        props = dom.getElementsByTagName('property')
        for p in props:
            pass
            #print '***', p.getAttribute('name'), p.childNodes[0].childNodes[0].data
        zf.close()
