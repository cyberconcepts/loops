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

from datetime import datetime
import os, re, stat

from zope.app.container.interfaces import INameChooser
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.contenttype import guess_content_type
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.interface import implements, Attribute
from zope.schema.interfaces import IField
from zope.traversing.api import getName, getParent

from cybertools.text import mimetypes
from cybertools.typology.interfaces import IType
from loops.common import AdapterBase, adapted
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

    def update(self):
        existing = self.context.getResources()
        # TODO: use full address for checking for existing resources
        old = dict((adapted(obj).uniqueAddress, obj) for obj in existing)
        #old = dict((adapted(obj).externalAddress, obj) for obj in existing)
        new = []
        oldFound = []
        provider = component.getUtility(IExternalCollectionProvider,
                                        name=self.providerName or '')
        for addr, mdate in provider.collect(self):
            if addr in old:
                # may be it would be better to return a file's hash
                # for checking for changes...
                oldFound.append(addr)
                if mdate > self.lastUpdated:
                    # force reindexing
                    notify(ObjectModifiedEvent(old[addr]))
            else:
                new.append(addr)
        if new:
            newResources = provider.createExtFileObjects(self, new)
            for r in newResources:
                self.context.assignResource(r)
        for addr in old:
            if addr not in oldFound:
                # not part of the collection any more
                # TODO: only remove from collection but keep object?
                self.remove(old[addr])
        self.lastUpdated = datetime.today()

    def clear(self):
        for obj in self.context.getResources():
            self.remove(obj)

    def remove(self, obj):
        del self.resourceManager[getName(obj)]

    @Lazy
    def resourceManager(self):
        return self.context.getLoopsRoot().getResourceManager()


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
                    mtime = os.stat(os.path.join(path, f))[stat.ST_MTIME]
                    yield (os.path.join(path[len(directory)+1:], f),
                           datetime.fromtimestamp(mtime))

    def createExtFileObjects(self, client, addresses, extFileType=None):
        if extFileType is None:
            extFileType = client.context.getLoopsRoot().getConceptManager()['extfile']
        container = client.context.getLoopsRoot().getResourceManager()
        directory = self.getDirectory(client)
        for addr in addresses:
            name = self.generateName(container, addr)
            title = self.generateTitle(addr)
            obj = addAndConfigureObject(
                            container, Resource, name,
                            title=title,
                            resourceType=extFileType,
                            externalAddress=addr,
                            storageName='fullpath',
                            storageParams=dict(subdirectory=directory),
                            contentType = guess_content_type(addr,
                                    default='application/octet-stream')[0]
                            )
            yield obj

    def getDirectory(self, client):
        baseAddress = client.baseAddress or ''
        address = client.address or ''
        return os.path.join(baseAddress, address)

    def generateName(self, container, name):
        name = INameChooser(container).chooseName(name, None)
        return name

    def generateTitle(self, title):
        title = os.path.split(title)[-1]
        if '.' in title:
            base, ext = title.rsplit('.', 1)
            if ext.lower() in mimetypes.extensions.values():
                title = base
        return title.decode('UTF-8')
