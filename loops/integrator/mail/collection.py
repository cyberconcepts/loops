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
Concept adapter(s) for external collections, e.g. a directory in the
file system.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.interface import implements

from loops.integrator.collection import ExternalCollectionAdapter
from loops.integrator.mail.interfaces import IMailCollection
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IMailCollection,)


class MailCollectionAdapter(ExternalCollectionAdapter):
    """ A concept adapter for accessing a mail collection.
        May delegate access to a named utility.
    """

    implements(IMailCollection)

    _adapterAttributes = ExternalCollectionAdapter._adapterAttributes + (
                            'providerName', '_collectedObjects')
    _contextAttributes = list(IMailCollection)

    _collectedObjects = None

    def getProviderName(self):
        return getattr(self.context, '_providerName', None) or u'imap'
    def setProviderName(self, value):
        self.context._providerName = value
    providerName = property(getProviderName, setProviderName)
