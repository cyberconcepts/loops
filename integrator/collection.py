#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Concept adapter(s) for external collections, e.g. a directory in the
file system.

$Id$
"""

import os, re
from zope.component import adapts
from zope.interface import implements, Attribute
from zope.cachedescriptors.property import Lazy
from zope.schema.interfaces import IField
from zope.traversing.api import getName, getParent

from cybertools.typology.interfaces import IType
from loops.common import AdapterBase
from loops.interfaces import IResource, IConcept
from loops.integrator.interfaces import IExternalCollection
from loops.integrator.interfaces import IExternalCollectionProvider
from loops.resource import Resource
from loops.setup import addAndConfigureObject
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IExternalCollection,)


class ExternalCollectionAdapter(AdapterBase):
    """ A concept adapter for accessing an external collection.
        May delegate access to a named utility.
    """

    implements(IExternalCollection)
    adapts(IConcept)

    _adapterAttributes = ('context', '__parent__',)
    _contextAttributes = list(IExternalCollection) + list(IConcept)

    def create(self):
        pass

    def update(self):
        pass


class DirectoryCollectionProvider(object):
    """ A utility that provides access to files in a directory.
    """

    implements(IExternalCollectionProvider)

    def collect(self, client):
        directory = self.getDirectory(client)
        pattern = re.compile(client.pattern or '.*')
        for path, dirs, files in os.walk(directory):
            if '.svn' in dirs:
                del dirs[dirs.index('.svn')]
            for f in files:
                if pattern.match(f):
                    yield os.path.join(path[len(directory)+1:], f)

    def createExtFileObjects(self, client, addresses, extFileType=None):
        if extFileType is None:
            extFileType = client.context.getLoopsRoot().getConceptManager()['extfile']
        rm = client.context.getLoopsRoot().getResourceManager()
        directory = self.getDirectory(client)
        for addr in addresses:
            name = addr
            obj = addAndConfigureObject(
                            rm, Resource, name,
                            title=addr.decode('UTF-8'),
                            type=extFileType,
                            externalAddress=addr,
                            storage='fullpath',
                            storageParams=dict(subdirectory=directory))
            yield obj

    def getDirectory(self, client):
        baseAddress = client.baseAddress or ''
        address = client.address or ''
        return os.path.join(baseAddress, address)

