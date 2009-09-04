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
from logging import getLogger

from zope.app.container.interfaces import INameChooser
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.interface import implements
from zope.traversing.api import getName, getParent

from loops.common import AdapterBase, adapted
from loops.interfaces import IResource, IConcept
from loops.integrator.interfaces import IExternalCollectionProvider
from loops.integrator.mail.system import IMAP4
from loops.resource import Resource
from loops.setup import addAndConfigureObject


class IMAPCollectionProvider(object):
    """ A utility that provides access to an IMAP folder.
    """

    implements(IExternalCollectionProvider)

    def collect(self, client):
        client._collectedObjects = {}
        imap = IMAP4(client.baseAddress)
        imap.login(client.userName, client.password)
        mailbox = 'INBOX'
        addr = client.address
        if addr:
            mailbox = mailbox + '.' + addr.replace('/', '.')
        imap.select(mailbox)
        type, data = imap.search(None, 'ALL')
        for num in data[0].split():
            type, data = imap.fetch(num, '(RFC822)')
            externalAddress = num
            obj = data
            mtime = datetime.today()
            client._collectedObjects[externalAddress] = obj
            yield externalAddress, mtime

    def createExtFileObjects(self, client, addresses, extFileTypes=None):
        loopsRoot = client.context.getLoopsRoot()
        container = loopsRoot.getResourceManager()
        contentType = 'text/plain'
        resourceType = loopsRoot.getConceptManager()['email']
        for addr in addresses:
            print '***', addr, client._collectedObjects[addr]
        return []

    def _dummy(self):
            name = self.generateName(container, addr)
            title = self.generateTitle(addr)
            obj = addAndConfigureObject(
                            container, Resource, name,
                            title=title,
                            resourceType=extFileType,
                            contentType=contentType,
            )
            yield obj
