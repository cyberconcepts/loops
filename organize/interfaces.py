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
from zope import component, schema
from zope.app import zapi
from zope.app.principalannotation import annotations
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.i18nmessageid import MessageFactory
from cybertools.organize.interfaces import IPerson as IBasePerson

_ = MessageFactory('zope')

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
        if not userId:
            return
        auth = component.getUtility(IAuthentication, context=self.context)
        try:
            principal = auth.getPrincipal(userId)
        except PrincipalLookupError:
            raiseValidationError(u'User %s does not exist' % userId)
        pa = annotations(principal)
        person = pa.get(ANNOTATION_KEY, None)
        if person is not None and person != self.context:
            raiseValidationError(
                u'There is alread a person (%s) assigned to user %s.'
                % (zapi.getName(person), userId))


class IPerson(IBasePerson):
    """ Resembles a human being with a name (first and last name),
        a birth date, and a set of addresses. This interface only
        lists fields used in addidtion to those provided by the
        basic cybertools.organize package.
    """

    userId = UserId(
                    title=_(u'User ID'),
                    description=_(u'The principal id of a user that should '
                                   'be associated with this person.'),
                    required=False,)
