# loops.organize.party

""" Adapters for IConcept providing interfaces from the cybertools.organize package.
"""

from persistent.mapping import PersistentMapping
from zope import interface, component
from zope.principalannotation.utility import annotations
from zope.authentication.interfaces import IAuthentication, PrincipalLookupError
from zope.authentication.interfaces import IUnauthenticatedPrincipal
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.formlib.interfaces import WidgetInputError
from zope.interface import implementer
from zope.schema.interfaces import ValidationError
from zope.security.proxy import removeSecurityProxy
from zope.traversing.api import getName

from cybertools.organize.party import Person as BasePerson
from cybertools.relation.interfaces import IRelationRegistry
from cybertools.typology.interfaces import IType
from loops.common import AdapterBase, baseObject
from loops.concept import Concept
from loops.interfaces import IConcept
from loops.organize.interfaces import IAddress, IPerson, IHasRole
from loops.organize.interfaces import ANNOTATION_KEY
from loops.predicate import RelationAdapter
from loops.predicate import PredicateInterfaceSourceList
from loops.security.common import assignOwner, removeOwner, allowEditingForOwner
from loops.security.common import assignPersonRole, removePersonRole
from loops.security.common import getCurrentPrincipal
from loops.security.interfaces import ISecuritySetter
from loops.type import TypeInterfaceSourceList
from loops import util


# register type interfaces - (TODO: use a function for this)

TypeInterfaceSourceList.typeInterfaces += (IPerson, IAddress)
PredicateInterfaceSourceList.predicateInterfaces += (IHasRole,)


def getPersonForUser(context, request=None, principal=None):
    if context is None:
        return None
    if principal is None:
        if request is not None:
            principal = getattr(request, 'principal', None)
        else:
            principal = getPrincipal(context)
    if principal is None:
        return None
    loops = baseObject(context).getLoopsRoot()
    pa = annotations(principal).get(ANNOTATION_KEY, None)
    if pa is None:
        return None
    if type(pa) == Concept: # backward compatibility
        if pa.getLoopsRoot() == loops:
            return  pa
        else:
            return None
    return pa.get(util.getUidForObject(loops))


def getPrincipal(context):
    principal = getCurrentPrincipal()
    if principal is not None:
        if IUnauthenticatedPrincipal.providedBy(principal):
            return None
        return principal
    return None


@implementer(IPerson)
class Person(AdapterBase, BasePerson):
    """ typeInterface adapter for concepts of type 'person'.
    """

    _adapterAttributes = ('context', '__parent__', 'userId', 'phoneNumbers')
    _contextAttributes = list(IPerson) + list(IConcept)

    def getUserId(self):
        return getattr(self.context, '_userId', None)
    def setUserId(self, userId):
        setter = ISecuritySetter(self)
        if userId:
            principal = self.getPrincipalForUserId(userId)
            if principal is None:
                return
            person = getPersonForUser(self.context, principal=principal)
            if person is not None and person != self.context:
                name = getName(person)
                if name:
                    raise ValueError(
                        'There is already a person (%s) assigned to user %s.'
                        % (getName(person), userId))
            pa = annotations(principal)
            loopsId = util.getUidForObject(self.context.getLoopsRoot())
            ann = pa.get(ANNOTATION_KEY)
            if ann is None: # or not isinstance(ann, PersistentMapping):
                ann = pa[ANNOTATION_KEY] = PersistentMapping()
            ann[loopsId] = self.context
            #assignOwner(self.context, userId)
            assignPersonRole(self.context, userId)
        oldUserId = self.userId
        if oldUserId and oldUserId != userId:
            self.removeReferenceFromPrincipal(oldUserId)
            removeOwner(self.context, oldUserId)
            removePersonRole(self.context, oldUserId)
        self.context._userId = userId
        setter.propagateSecurity()
        allowEditingForOwner(self.context, revert=not userId)  # why this?
    userId = property(getUserId, setUserId)

    def removeReferenceFromPrincipal(self, userId):
        principal = self.getPrincipalForUserId(userId)
        if principal is not None:
            pa = annotations(principal)
            ann = pa.get(ANNOTATION_KEY)
            if type(ann) == Concept: # backward compatibility
                pa[ANNOTATION_KEY] = None
            else:
                if ann is not None:
                    loopsId = util.getUidForObject(self.context.getLoopsRoot())
                    ann[loopsId] = None

    def getPhoneNumbers(self):
        return getattr(self.context, '_phoneNumbers', [])
    def setPhoneNumbers(self, value):
        self.context._phoneNumbers = value
    phoneNumbers = property(getPhoneNumbers, setPhoneNumbers)

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


@implementer(IAddress)
class Address(AdapterBase):
    """ typeInterface adapter for concepts of type 'address'.
    """

    _adapterAttributes = ('context', '__parent__', 'lines')
    _contextAttributes = list(IAddress) + list(IConcept)

    def getLines(self):
        return getattr(self.context, '_lines', None) or []
    def setLines(self, value):
        self.context._lines = value
    lines = property(getLines, setLines)


@implementer(IHasRole)
class HasRole(RelationAdapter):
    """ Allows specification of a role for a relation.
    """

    _contextAttributes = list(IHasRole)
