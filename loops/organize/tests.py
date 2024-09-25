
import unittest, doctest
from zope.interface.verify import verifyClass

from zope import component
from zope.app.appsetup.bootstrap import ensureUtility
from zope.authentication.interfaces import IAuthentication
from zope.pluggableauth import PluggableAuthentication
from zope.pluggableauth.interfaces import IAuthenticatorPlugin
from zope.pluggableauth.factories import FoundPrincipalFactory
from zope.pluggableauth.factories import Principal
from zope.pluggableauth.plugins.principalfolder import InternalPrincipal
from zope.pluggableauth.plugins.principalfolder import PrincipalFolder
from zope.principalannotation.utility import PrincipalAnnotationUtility
from zope.principalannotation.utility import annotations
from zope.principalannotation.interfaces import IPrincipalAnnotationUtility
from zope.principalregistry.principalregistry import PrincipalRegistry
from zope.securitypolicy.interfaces import IRolePermissionManager
from zope.securitypolicy.interfaces import IPrincipalRoleManager

from cybertools.util.jeep import Jeep
from loops.common import adapted
from loops.concept import Concept
from loops.organize.interfaces import IPerson, IHasRole
from loops.organize.interfaces import IEvent, IAgendaItem
from loops.organize.party import Person, HasRole
from loops.organize.task import Task, Event, AgendaItem
from loops.setup import addAndConfigureObject
from loops.tests.auth import login


def setupUtilitiesAndAdapters(loopsRoot):
    auth = PrincipalRegistry()
    component.provideUtility(auth, IAuthentication)
    principalAnnotations = PrincipalAnnotationUtility()
    component.provideUtility(principalAnnotations, IPrincipalAnnotationUtility)
    component.provideAdapter(Person, provides=IPerson)
    component.provideAdapter(Task)
    component.provideAdapter(Event, provides=IEvent)
    component.provideAdapter(AgendaItem, provides=IAgendaItem)
    component.provideAdapter(FoundPrincipalFactory)
    component.provideAdapter(HasRole, provides=IHasRole)
    return Jeep((
            ('auth', auth),
            ('principalAnnotations', principalAnnotations),
            ('rolePermissions', IRolePermissionManager(loopsRoot)),
            ('principalRoles', IPrincipalRoleManager(loopsRoot)),
    ))

def setupObjectsForTesting(site, concepts):
    loopsRoot = concepts.getLoopsRoot()
    setupData = setupUtilitiesAndAdapters(loopsRoot)
    ensureUtility(site, IAuthentication, '', PluggableAuthentication,
                  copy_to_zlog=False)
    pau = component.getUtility(IAuthentication, context=site)
    # create principal folder and user(s)
    pFolder = PrincipalFolder('users.')
    pau['users'] = pFolder
    pau.authenticatorPlugins = ('users',)
    pFolder['john'] = InternalPrincipal('john', 'xx', u'John')
    # create person and log in
    johnC = addAndConfigureObject(concepts, Concept, 'john',
                conceptType=concepts['person'], title=u'john', userId='users.john')
    pJohn = Principal('users.john', 'xxx', u'John')
    login(pJohn)
    # grant roles and permissions
    grantPermission = setupData.rolePermissions.grantPermissionToRole
    assignRole = setupData.principalRoles.assignRoleToPrincipal
    grantPermission('zope.View', 'zope.Member')
    assignRole('zope.Member', 'users.john')
    setupData.update(dict(johnC=johnC))
    return setupData


class Test(unittest.TestCase):
    "Basic tests for the organize sub-package."

    def testSomething(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                doctest.DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
