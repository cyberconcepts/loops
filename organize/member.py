#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
"""

from zope import interface, component, schema
from zope.app.component import queryNextUtility
from zope.app.container.interfaces import INameChooser
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements
from zope.app.authentication.interfaces import IPluggableAuthentication
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.authentication.principalfolder import IInternalPrincipal
from zope.app.authentication.principalfolder import InternalPrincipal
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.event import notify
from zope.i18nmessageid import MessageFactory
from zope.cachedescriptors.property import Lazy

from cybertools.meta.interfaces import IOptions
from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.concept import Concept
from loops.interfaces import ILoops
from loops.organize.auth import IPersonBasedAuthenticator
from loops.organize.interfaces import IMemberRegistrationManager
from loops.organize.util import getPrincipalFolder, getGroupsFolder
from loops.organize.util import getInternalPrincipal
from loops.type import getOptionsDict
from loops.util import _


class MemberRegistrationManager(object):

    implements(IMemberRegistrationManager)
    adapts(ILoops)

    person_typeName = 'person'
    default_principalfolder = 'loops'
    principalfolder_key = u'registration.principalfolder'
    groups_key = u'registration.groups'

    def __init__(self, context):
        self.context = context

    @Lazy
    def personType(self):
        concepts = self.context.getConceptManager()
        return adapted(concepts[self.person_typeName])

    def getPrincipalFolderFromOption(self):
        options = IOptions(self.personType)
        pfName = options(self.principalfolder_key,
                         (self.default_principalfolder,))[0]
        return getPrincipalFolder(self.context, pfName)

    def register(self, userId, password, lastName, firstName=u'',
                 groups=[], useExisting=False, pfName=None, **kw):
        options = IOptions(self.personType)
        if pfName is None:
            pfName = options(self.principalfolder_key,
                             (self.default_principalfolder,))[0]
        self.createPrincipal(pfName, userId, password, lastName, firstName, 
                             useExisting=useExisting)
        if not groups:
            groups = options(self.groups_key, ())
        self.setGroupsForPrincipal(pfName, userId,  groups=groups)
        return self.createPersonForPrincipal(pfName, userId, lastName, firstName,
                                      useExisting, **kw)

    def createPrincipal(self, pfName, userId, password, lastName,
                              firstName=u'', groups=[], useExisting=False,
                              overwrite=False, **kw):
        pFolder = getPrincipalFolder(self.context, pfName)
        if IPersonBasedAuthenticator.providedBy(pFolder):
             pFolder.setPassword(userId, password)
        else:
            title = firstName and ' '.join((firstName, lastName)) or lastName
            principal = InternalPrincipal(userId, password, title)
            if overwrite:
                if userId in pFolder:
                    principal = pFolder[userId]
                    principal.password = password
                    if title:
                        principal.title = title
                else:
                    pFolder[userId] = principal
            elif useExisting:
                if userId not in pFolder:
                    pFolder[userId] = principal
            else:
                if userId in pFolder:
                    return dict(fieldName='loginName', error='duplicate_loginname')
                else:
                    pFolder[userId] = principal

    def setGroupsForPrincipal(self, pfName, userId, groups=[]):
        pFolder = getPrincipalFolder(self.context, pfName)
        for groupInfo in groups:
            names = groupInfo.split(':')
            if len(names) == 1:
                gName, gfName = names[0], None
            else:
                gName, gfName = names
            gFolder = getGroupsFolder(gfName)
            if gFolder is not None:
                group = gFolder.get(gName)
                if group is not None:
                    members = list(group.principals)
                    members.append(pFolder.prefix + userId)
                    group.principals = members

    def createPersonForPrincipal(self, pfName, userId, lastName, firstName=u'',
                                 useExisting=False, **kw):
        concepts = self.context.getConceptManager()
        personType = adapted(concepts[self.person_typeName])
        pFolder = getPrincipalFolder(self.context, pfName)
        title = firstName and ' '.join((firstName, lastName)) or lastName
        name = baseId = 'person.' + userId
        if useExisting and name in concepts:
            person = concepts[name]
        else:
            person = Concept(title)
            name = INameChooser(concepts).chooseName(name, person)
            concepts[name] = person
        person.conceptType = personType.context
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
        if not IInternalPrincipal.providedBy(principal):
            principal = getInternalPrincipal(principal.id)
        if not principal.checkPassword(oldPw):
            return False
        principal.setPassword(newPw)
        return True

