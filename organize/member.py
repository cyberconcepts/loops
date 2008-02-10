#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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

from zope import interface, component, schema
from zope.app.component import queryNextUtility
from zope.component import adapts
from zope.interface import implements
from zope.app.authentication.interfaces import IPluggableAuthentication
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.authentication.principalfolder import InternalPrincipal
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.event import notify
from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.concept import Concept
from loops.interfaces import ILoops
from loops.organize.interfaces import IMemberRegistrationManager
from loops.organize.util import getPrincipalFolder, getGroupsFolder
from loops.organize.util import getInternalPrincipal
from loops.type import getOptionsDict
from loops.util import _


class MemberRegistrationManager(object):

    implements(IMemberRegistrationManager)
    adapts(ILoops)

    def __init__(self, context):
        self.context = context

    def register(self, userId, password, lastName, firstName=u'',
                 groups=[], useExisting=False, **kw):
        # step 1: create an internal principal in the loops principal folder:
        pFolder = getPrincipalFolder(self.context)
        title = firstName and ' '.join((firstName, lastName)) or lastName
        principal = InternalPrincipal(userId, password, title)
        if useExisting:
            if userId not in pFolder:
                pFolder[userId] = principal
        else:
            pFolder[userId] = principal
        # step 2 (optional): assign to group(s)
        personType = self.context.getLoopsRoot().getConceptManager()['person']
        od = getOptionsDict(adapted(personType).options)
        groupInfo = od.get('group')
        if groupInfo:
            gfName, groupNames = groupInfo.split(':')
            gFolder = getGroupsFolder(gfName)
            if not groups:
                groups = groupNames.split(',')
        else:
            gFolder = getGroupsFolder()
        if gFolder is not None:
            for g in groups:
                group = gFolder.get(g)
                if group is not None:
                    members = list(group.principals)
                    members.append(pFolder.prefix + userId)
                    group.principals = members
        # step 3: create a corresponding person concept:
        cm = self.context.getConceptManager()
        id = baseId = 'person.' + userId
        # TODO: use NameChooser
        if useExisting and id in cm:
            person = cm[id]
        else:
            num = 0
            while id in cm:
                num +=1
                id = baseId + str(num)
            person = cm[id] = Concept(title)
        person.conceptType = cm['person']
        personAdapter = adapted(person)
        personAdapter.firstName = firstName
        personAdapter.lastName = lastName
        personAdapter.userId = pFolder.prefix + userId
        for k, v in kw.items():
            setattr(personAdapter, k, v)
        notify(ObjectCreatedEvent(person))
        notify(ObjectModifiedEvent(person))
        return personAdapter

    def changePassword(self, principal, oldPw, newPw):
        if not isinstance(principal, InternalPrincipal):
            principal = getInternalPrincipal(principal.id)
        if not principal.checkPassword(oldPw):
            return False
        principal.setPassword(newPw)
        return True

