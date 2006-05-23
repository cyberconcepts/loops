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
Member registration adapter(s).

$Id$
"""

from zope.app import zapi
from zope import interface, component, schema
from zope.component import adapts
from zope.interface import implements
from zope.app.authentication.interfaces import IPluggableAuthentication
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.authentication.principalfolder import InternalPrincipal
from zope.app.event.objectevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.security.interfaces import IAuthentication
from zope.event import notify
from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from loops.interfaces import ILoops
from loops.concept import Concept
from loops.organize.interfaces import IMemberRegistrationManager
from loops.organize.util import getPrincipalFolder, authPluginId

_ = MessageFactory('zope')


class MemberRegistrationManager(object):

    implements(IMemberRegistrationManager)
    adapts(ILoops)

    def __init__(self, context):
        self.context = context

    def register(self, userId, password, lastName, firstName=u'', **kw):
        # step 1: create an internal principal in the loops principal folder:
        pFolder = getPrincipalFolder(self.context)
        title = firstName and ' '.join((firstName, lastName)) or lastName
        # TODO: care for password encryption:
        principal = InternalPrincipal(userId, password, title)
        pFolder[userId] = principal
        # step 2: create a corresponding person concept:
        cm = self.context.getConceptManager()
        id = baseId = 'person.' + userId
        num = 0
        while id in cm:
            num +=1
            id = baseId + str(num)
        person = cm[id] = Concept(title)
        # TODO: the name of the person type object must be kept flexible!
        # So we have to search for a type concept that has IPerson as
        # its typeInterface...
        person.conceptType = cm['person']
        personAdapter = IType(person).typeInterface(person)
        personAdapter.firstName = firstName
        personAdapter.lastName = lastName
        personAdapter.userId = '.'.join((authPluginId, userId))
        notify(ObjectCreatedEvent(person))
        notify(ObjectModifiedEvent(person))
        return personAdapter

    def changePassword(self, oldPw, newPw):
        pass

