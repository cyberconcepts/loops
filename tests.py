# $Id$

import unittest
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass
from zope.interface import implements
from zope.app import zapi
from zope.app.intid.interfaces import IIntIds

from interfaces import IConcept
from concept import Concept

class Test(unittest.TestCase):
    "Basic tests for the loops package."

    def testInterfaces(self):
        verifyClass(IConcept, Concept)
        self.assert_(IConcept.providedBy(Concept()))


def test_suite():
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                DocFileSuite('README.txt'),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
