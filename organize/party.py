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

from zope import interface, component
from zope.app import zapi
from zope.app.principalannotation import annotations
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.schema.interfaces import ValidationError
from zope.app.form.interfaces import WidgetInputError
from zope.security.proxy import removeSecurityProxy

from cybertools.organize.party import Person as BasePerson
from cybertools.typology.interfaces import IType
from loops.interfaces import IConcept
from loops.organize.interfaces import IPerson, ANNOTATION_KEY
from loops.type import TypeInterfaceSourceList


# register IPerson as a type interface - (TODO: use a function for this)

TypeInterfaceSourceList.typeInterfaces += (IPerson,)


class Person(BasePerson):
    """ typeInterface adapter for concepts of type 'person'.
    """

    implements(IPerson)
    adapts(IConcept)

    __attributes = ('context', '__parent__', 'userId',)
    __schemas = list(IPerson) + list(IConcept)

    def __init__(self, context):
        self.context = context # to get the permission stuff right
        self.__parent__ = context

    def __getattr__(self, attr):
        self.checkAttr(attr)
        return getattr(self.context, '_' + attr, None)

    def __setattr__(self, attr, value):
        if attr in self.__attributes:
            object.__setattr__(self, attr, value)
        else:
            self.checkAttr(attr)
            setattr(self.context, '_' + attr, value)

    def checkAttr(self, attr):
        if attr not in self.__schemas:
            raise AttributeError(attr)

    def getUserId(self):
        return getattr(self.context, '_userId', None)
    def setUserId(self, userId):
        auth = self.authentication
        if userId:
            principal = auth.getPrincipal(userId)
            pa = annotations(principal)
            person = pa.get(ANNOTATION_KEY, None)
            if person is not None and person != self.context:
                raise ValueError(
                    'There is alread a person (%s) assigned to user %s.'
                    % (zapi.getName(person), userId))
            pa[ANNOTATION_KEY] = self.context
        oldUserId = self.userId
        if oldUserId and oldUserId != userId:
            self.removeReferenceFromPrincipal(oldUserId)
        self.context._userId = userId
    userId = property(getUserId, setUserId)

    def removeReferenceFromPrincipal(self, userId):
        principal = self.getPrincipalForUserId(userId)
        if principal is not None:
            pa = annotations(principal)
            pa[ANNOTATION_KEY] = None

    @Lazy
    def authentication(self):
        return getAuthenticationUtility(self.context)

    @Lazy
    def principal(self):
        return self.getPrincipalForUserId()

    def getPrincipalForUserId(self, userId=None):
        userId = userId or self.userId
        if not userId:
            return None
        auth = self.authentication
        try:
            return auth.getPrincipal(userId)
        except PrincipalLookupError:
            return None

    def getPrincipalForUserId(self, userId=None):
        userId = userId or self.userId
        if not userId:
            return None
        auth = self.authentication
        try:
            return auth.getPrincipal(userId)
        except PrincipalLookupError:
            return None


def getAuthenticationUtility(context):
    return component.getUtility(IAuthentication, context=context)


def removePersonReferenceFromPrincipal(context, event):
    """ Handles IObjectRemoved event for concepts used as persons.
    """
    if IConcept.providedBy(context):
        # this does not work as the context is already removed from the
        # relation registry:
        #if IType(context).typeInterface == IPerson:
        #    person = IPerson(context)
        #    if person.userId:
        if getattr(context, '_userId', None):
            person = IPerson(context)
            person.removeReferenceFromPrincipal(person.userId)

