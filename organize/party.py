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
Adapters for IConcept providing interfaces from the cybertools.organize package.

$Id$
"""

from zope.app import zapi
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy

from cybertools.organize.interfaces import IPerson
from loops.interfaces import IConcept
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IPerson,)


class Person(object):
    """ typeInterface adapter for concepts of type 'person'.
    """

    implements(IPerson)
    adapts(IConcept)

    def __init__(self, context):
        self.context = context
        self.__parent__ = context  # to get the permission stuff right

    def getFirstName(self):
        return getattr(self.context, '_firstName', u'')
    def setFirstName(self, firstName):
        self.context._firstName = firstName
    firstName = property(getFirstName, setFirstName)

    def getLastName(self):
        return getattr(self.context, '_lastName', u'')
    def setLastName(self, lastName):
        self.context._lastName = lastName
    lastName = property(getLastName, setLastName)

    def getBirthDate(self):
        return getattr(self.context, '_birthDate', u'')
    def setBirthDate(self, birthDate):
        self.context._birthDate = birthDate
    birthDate = property(getBirthDate, setBirthDate)



