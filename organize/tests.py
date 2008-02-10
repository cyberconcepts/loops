# $Id$

import unittest, doctest
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass

from zope import component
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility
from zope.app.principalannotation import PrincipalAnnotationUtility
from zope.app.principalannotation import annotations
from zope.app.security.interfaces import IAuthentication
from zope.app.security.principalregistry import PrincipalRegistry
from zope.app.securitypolicy.interfaces import IRolePermissionManager
from zope.app.securitypolicy.interfaces import IPrincipalRoleManager

from cybertools.util.jeep import Jeep
from loops.organize.interfaces import IPerson
from loops.organize.party import Person


def setupUtilitiesAndAdapters(loopsRoot):
    auth = PrincipalRegistry()
    component.provideUtility(auth, IAuthentication)
    principalAnnotations = PrincipalAnnotationUtility()
    component.provideUtility(principalAnnotations, IPrincipalAnnotationUtility)
    component.provideAdapter(Person, provides=IPerson)
    return Jeep((
            ('auth', auth),
            ('principalAnnotations', principalAnnotations),
            ('rolePermissions', IRolePermissionManager(loopsRoot)),
            ('principalRoles', IPrincipalRoleManager(loopsRoot)),
    ))


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
