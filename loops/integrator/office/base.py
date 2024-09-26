# loops.integrator.office.base

""" Resource adapter(s) for MS Office files.
"""

from datetime import date, datetime, timedelta
from logging import getLogger
from lxml import etree
import os
import shutil
from time import strptime
from zipfile import ZipFile, BadZipfile
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.interface import implementer
from zope.traversing.api import getName, getParent

from cybertools.storage.interfaces import IExternalStorage
from loops.common import AdapterBase, adapted
from loops.integrator.interfaces import IOfficeFile
from loops.interfaces import IResource, IExternalFile
from loops.resource import ExternalFileAdapter
from loops.type import TypeInterfaceSourceList
from loops.versioning.interfaces import IVersionable


TypeInterfaceSourceList.typeInterfaces += (IOfficeFile,)


@implementer(IOfficeFile)
class OfficeFile(ExternalFileAdapter):
    """ An external file that references a MS Office (2007/2010) file.
        It provides access to the document content and properties.
    """

    _adapterAttributes = (ExternalFileAdapter._adapterAttributes + 
                            ('documentPropertiesAccessible',))

    propertyMap = {u'Revision:': 'version'}
    propFileName = 'docProps/custom.xml'
    corePropFileName = 'docProps/core.xml'
    fileExtensions = ('.docm', '.docx', 'dotm', 'dotx', 'pptx', 'potx', 'ppsx',
                      '.xlsm', '.xlsx', '.xltm', '.xltx')

    def getDocumentPropertiesAccessible(self):
        return getattr(self.context, '_documentPropertiesAccessible', True)
    def setDocumentPropertiesAccessible(self, value):
        self.context._documentPropertiesAccessible = value
    documentPropertiesAccessible = property(
                getDocumentPropertiesAccessible, setDocumentPropertiesAccessible)

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

    @Lazy
    def docFilename(self):
        subDir = self.storageParams.get('subdirectory')
        return self.storage.getDir(self.externalAddress, subDir)

    @Lazy
    def docPropertyDom(self):
        fn = self.docFilename
        result = dict(core=[], custom=[])
        if not os.path.exists(fn):
            # may happen before file has been created
            return result
        root, ext = os.path.splitext(fn)
        if not ext.lower() in self.fileExtensions:
            return result
        try:
            zf = ZipFile(fn, 'r')
            self.documentPropertiesAccessible = True
        except (IOError, BadZipfile) as e:
            from logging import getLogger
            self.logger.warn(e)
            self.documentPropertiesAccessible = False
            return result
        if self.corePropFileName not in zf.namelist():
            self.logger.warn('Core properties not found in file %s.' %
                             self.externalAddress)
        else:
            result['core'] = etree.fromstring(zf.read(self.corePropFileName))
        if self.propFileName not in zf.namelist():
            self.logger.warn('Custom properties not found in file %s.' %
                             self.externalAddress)
        else:
            result['custom'] = etree.fromstring(zf.read(self.propFileName))
        zf.close()
        return result

    def getDocProperty(self, pname):
        for p in self.docPropertyDom['custom']:
            name = p.attrib.get('name')
            if name == pname:
                return p[0].text
        return None

    def getCoreProperty(self, pname):
        for p in self.docPropertyDom['core']:
            if p.tag.endswith(pname):
                return p.text
        return None

    def processDocument(self):
        changed = False
        docVersion = None
        version = IVersionable(self.context).versionId
        strType = ('{http://schemas.openxmlformats.org/'
                   'officeDocument/2006/docPropsVTypes}lpwstr')
        attributes = {}
        # get dc:description from core.xml
        desc = self.getCoreProperty('description')
        if not self.documentPropertiesAccessible:
            return
        if desc is not None:
            attributes['comments'] = desc
        dom = self.docPropertyDom['custom']
        for p in dom:
            name = p.attrib.get('name')
            value = p[0].text
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
        fn = self.docFilename
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
        errors = self.update(attributes)
        if errors:
            self.processingErrors = errors

    def update(self, attributes):
        # to be implemented by subclass
        pass


def parseDate(s):
    if not s:
        return None
    try:
        tt = strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        return None
    #    try:
    #        tt = strptime(s, '%d.%m.%y')
    #    except ValueError:
    #        tt = strptime(s, '%d.%m.%Y')
    dt = datetime(*tt[:6]) + timedelta(hours=2)
    return date(dt.year, dt.month, dt.day)
    #return date(*strptime(s, '%Y-%m-%dT%H:%M:%SZ')[:3])

