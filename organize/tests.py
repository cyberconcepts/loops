# $Id$

import unittest, doctest
from zope.testing.doctestunit import DocFileSuite
from zope.interface.verify import verifyClass

from zope import component
from zope.app.appsetup.bootstrap import ensureUtility
from zope.app.authentication.authentication import PluggableAuthentication
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.authentication.principalfolder import FoundPrincipalFactory
from zope.app.authentication.principalfolder import InternalPrincipal
from zope.app.authentication.principalfolder import Principal
from zope.app.authentication.principalfolder import PrincipalFolder
from zope.app.principalannotation import PrincipalAnnotationUtility
from zope.app.principalannotation import annotations
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility
from zope.app.security.interfaces import IAuthentication
from zope.app.security.principalregistry import PrincipalRegistry
from zope.securitypolicy.interfaces import IRolePermissionManager
from zope.securitypolicy.interfaces import IPrincipalRoleManager

from cybertools.util.jeep import Jeep
from loops.common import adapted
from loops.concept import Concept
from loops.organize.interfaces import IPerson, IHasRole
from loops.organize.party import Person, HasRole
from loops.organize.task import Task
from loops.setup import addAndConfigureObject
from loops.tests.auth import login


def setupUtilitiesAndAdapters(loopsRoot):
    auth = PrincipalRegistry()
    component.provideUtility(auth, IAuthentication)
    principalAnnotations = PrincipalAnnotationUtility()
    component.provideUtility(principalAnnotations, IPrincipalAnnotationUtility)
    component.provideAdapter(Person, provides=IPerson)
    component.provideAdapter(Task)
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
                  copy_to_zlog=False, asObject=True)
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
                DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
