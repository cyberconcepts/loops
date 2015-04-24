#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema
from zope.app import zapi
from zope.app.principalannotation import annotations
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.security.proxy import removeSecurityProxy

from cybertools.organize.interfaces import IAddress as IBaseAddress
from cybertools.organize.interfaces import IPerson as IBasePerson
from cybertools.organize.interfaces import ITask
from loops.interfaces import ILoopsAdapter, IConceptSchema, IRelationAdapter
from loops.interfaces import HtmlText
from loops.organize.util import getPrincipalFolder
from loops import util
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
    """ Obsolete, as member registration does not use zope.formlib any more.
        TODO: transfer validation to loops.organize.browser.
    """

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
            name = zapi.getName(person)
            if name:
                raiseValidationError(
                    _(u'There is already a person ($person) '
                      u'assigned to user $userId.',
                      mapping=dict(person=name,
                                   userId=userId)))


class LoginName(schema.TextLine):
    """ Obsolete, as member registration does not use zope.formlib any more.
        TODO: transfer validation to loops.organize.browser.
    """

    def _validate(self, userId):
        super(LoginName, self)._validate(userId)
        if userId in getPrincipalFolder(self.context):
            raiseValidationError(
                _(u'There is already a user with ID $userId.',
                  mapping=dict(userId=userId)))


class IPerson(IConceptSchema, IBasePerson, ILoopsAdapter):
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


class IAddress(IConceptSchema, IBaseAddress, ILoopsAdapter):
    """ See cybertools.organize.
    """


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


class IPasswordReset(Interface):

    loginName = schema.TextLine(title=_(u'User ID'),
                    description=_(u'Your login name.'),
                    required=True,)
    loginName.nostore = True


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
                             u'used for managing members of this loops site')

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

# task management, meeting minutes: task, event, agenda item

class ITask(IConceptSchema, ITask, ILoopsAdapter):

    pass


class IEvent(ITask):

    participants = schema.Text(
        title=_(u'Participants'),
        description=_(u'The names of the persons taking part in the event.'),
        default=u'',
        missing_value=u'',
        required=False)


class IAgendaItem(ILoopsAdapter):

    description = HtmlText(
        title=_(u'label_description'),
        description=_(u'desc_description'),
        default=u'',
        missing_value=u'',
        required=False)

    responsible = schema.TextLine(
        title=_(u'label_responsible'),
        description=_(u'desc_responsible'),
        default=u'',
        required=False)

    discussion = HtmlText(
        title=_(u'label_discussion'),
        description=_(u'desc_discussion'),
        default=u'',
        missing_value=u'',
        required=False)

    consequences = HtmlText(
        title=_(u'label_consequences'),
        description=_(u'desc_consequences'),
        default=u'',
        missing_value=u'',
        required=False)

    description.height = 10
    discussion.height = consequences.height = 7


# 'hasrole' predicate

class IHasRole(IRelationAdapter):

    role = schema.Choice(
            title=_(u'Role'),
            description=_(u'Specifies the kind of interaction a person or another '
                    u'party has with an institution, a task, or a project '
                    u'it is associated with.'),
            source=util.KeywordVocabulary((
                    ('member', _(u'Member')),
                    ('master', _(u'Master')),
                )),
            default='member',
            required=True)


# presence

class IPresence(Interface):
    """ Utility for getting information about active principals,
        mapping principal.id to timestamp of last activity.
    """

    def update(self, principalId):
        """ Update Dictionary of active users, by calling addPresentUser();
            automaticly check for inactive users by calling
            removeInactiveUsers().
        """

    def addPresentUser(self, principalId):
        """Add a user to dictionary of active users.
        """

    def removeInactiveUsers(self):
        """ Remove a user from dictionary of active users if user
            didn't interact for last min_until_logout minutes.
        """

    def getPresentUsers(self):
        """ Return list of titles of active users.
        """

    def removePresentUser(self, principalId):
        """ Remove user from dictionary of active users, e.g. when user logs out.
        """
