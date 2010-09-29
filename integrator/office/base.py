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

from datetime import date, datetime, timedelta
from logging import getLogger
from lxml import etree
import os
import shutil
from time import strptime
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
from loops.versioning.interfaces import IVersionable


TypeInterfaceSourceList.typeInterfaces += (IOfficeFile,)


class OfficeFile(ExternalFileAdapter):
    """ An external file that references a MS Office (2007/2010) file.
        It provides access to the document content and properties.
    """

    implements(IOfficeFile)

    propertyMap = {u'Revision:': 'version'}
    propFileName = 'docProps/custom.xml'
    fileExtensions = ('.docm', '.docx', 'dotm', 'dotx',
                      '.xlsm', '.xlsx', '.xltm', '.xltx')

    @Lazy
    def logger(self):
        return getLogger('loops.integrator.office.base.OfficeFile')

    def setExternalAddress(self, addr):
        super(OfficeFile, self).setExternalAddress(addr)
        root, ext = os.path.splitext(self.externalAddress)
        if ext.lower() in self.fileExtensions:
            self.processDocument()
    externalAddress = property(ExternalFileAdapter.getExternalAddress,
                               setExternalAddress)

    def processDocument(self):
        subDir = self.storageParams.get('subdirectory')
        fn = self.storage.getDir(self.externalAddress, subDir)
        # open ZIP file, process properties, set version property in file
        try:
            zf = ZipFile(fn, 'r')
        except IOError, e:
            from logging import getLogger
            self.logger.warn(e)
            return
        #print '***', zf.namelist()
        if self.propFileName not in zf.namelist():
            self.logger.warn('Custom properties not found in file %s.' %
                             self.externalAddress)
        propsXml = zf.read(self.propFileName)
        dom = etree.fromstring(propsXml)
        changed = False
        docVersion = None
        version = IVersionable(self.context).versionId
        strType = ('{http://schemas.openxmlformats.org/'
                   'officeDocument/2006/docPropsVTypes}lpwstr')
        attributes = {}
        for p in dom:
            name = p.attrib.get('name')
            value = p[0].text
            #print '***', self.externalAddress, name, value, p[0].tag
            attr = self.propertyMap.get(name)
            if attr == 'version':
                docVersion = value
                if docVersion and docVersion != version:
                    # update XML
                    p[0] = etree.Element(strType)
                    p[0].text = version
                    changed = True
            elif attr is not None:
                attributes[attr] = value
        zf.close()
        if changed:
            newFn = fn + '.new'
            zf = ZipFile(fn, 'r')
            newZf = ZipFile(newFn, 'w')
            for info in zf.infolist():
                name = info.filename
                if name != self.propFileName:
                    newZf.writestr(info, zf.read(name))
            newZf.writestr(self.propFileName, etree.tostring(dom))
            newZf.close()
            shutil.move(newFn, fn)
        self.update(attributes)

    def update(self, attributes):
        # to be implemented by subclass
        pass


def parseDate(s):
    dt = datetime(*strptime(s, '%Y-%m-%dT%H:%M:%SZ')[:6]) + timedelta(hours=2)
    return date(dt.year, dt.month, dt.day)
    #return date(*strptime(s, '%Y-%m-%dT%H:%M:%SZ')[:3])

