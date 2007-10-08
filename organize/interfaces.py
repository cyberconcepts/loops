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
Interfaces for organizational stuff like persons and addresses.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema
from zope.app import zapi
from zope.app.principalannotation import annotations
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.security.proxy import removeSecurityProxy

from cybertools.organize.interfaces import IPerson as IBasePerson
from loops.organize.util import getPrincipalFolder, authPluginId
from loops.util import _

ANNOTATION_KEY = 'loops.organize.person'


class ValidationError(schema.interfaces.ValidationError):
    def doc(self):
        return self.info

def raiseValidationError(info):
    error = ValidationError()
    error.info = info
    raise error


class UserId(schema.TextLine):

    def _validate(self, userId):
        from loops.organize.party import getPersonForUser
        if not userId:
            return
        context = removeSecurityProxy(self.context).context
        auth = component.getUtility(IAuthentication, context=context)
        try:
            principal = auth.getPrincipal(userId)
        except PrincipalLookupError:
            raiseValidationError(_(u'User $userId does not exist',
                                   mapping={'userId': userId}))
        person = getPersonForUser(context, principal=principal)
        if person is not None and person != context:
            raiseValidationError(
                _(u'There is alread a person ($person) assigned to user $userId.',
                  mapping=dict(person=zapi.getName(person),
                               userId=userId)))


class LoginName(schema.TextLine):

    def _validate(self, userId):
        super(LoginName, self)._validate(userId)
        if userId in getPrincipalFolder(self.context):
            raiseValidationError(
                _(u'There is alread a user with ID $userId.',
                  mapping=dict(userId=userId)))


class IPerson(IBasePerson):
    """ Resembles a human being with a name (first and last name),
        a birth date, and a set of addresses. This interface only
        lists fields used in addition to those provided by the
        basic cybertools.organize package.
    """

    userId = UserId(title=_(u'User ID'),
                    description=_(u'The principal id (including prinicipal '
                                   'folder prefix) of a user that should '
                                   'be associated with this person.'),
                    required=False,)


class IPasswordEntry(Interface):

    password = schema.Password(title=_(u'Password'),
                    description=_(u'Enter password.'),
                    required=True,)
    passwordConfirm = schema.Password(title=_(u'Confirm password'),
                    description=_(u'Please repeat the password.'),
                    required=True,)
    password.nostore = True
    passwordConfirm.nostore = True


class IPasswordChange(IPasswordEntry):

    oldPassword = schema.Password(title=_(u'Old password'),
                    description=_(u'Enter old password.'),
                    required=True,)


class IMemberRegistration(IBasePerson, IPasswordEntry):
    """ Schema for registering a new member (user + person).
    """

    loginName = schema.TextLine(
                    title=_(u'User ID'),
                    description=_(u'Enter a user id.'),
                    required=True,)
    loginName.nostore = True


class IMemberRegistrationManager(Interface):
    """ Knows what to do for registrating a new member (portal user),
        change password, etc.
    """

    authPluginId = Attribute(u'The id of an authentication plugin to be '
                              'used for managing members of this loops site')

    def register(userId, password, lastName, firstName=u'', **kw):
        """ Register a new member for this loops site.
            Return the person adapter for the concept created.
            Raise Validation Error (?) if the user could not be created.
        """

    def changePassword(newPw):
        """ Change the password of the user currently logged-in.
            Raise a Validation Error (?) if the oldPw does not match the
            current password.
        """
