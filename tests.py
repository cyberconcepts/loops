# $Id$

import unittest
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass
from zope.interface import implements
from zope.app import zapi
from zope.app.intid.interfaces import IIntIds

from interfaces import ILoops
from loops import Loops
from interfaces import IConcept, IConceptManager
from loops.concept import Concept, ConceptManager

class Test(unittest.TestCase):
    "Basic tests for the loops package."

    def testInterfaces(self):
        verifyClass(ILoops, Loops)
        self.assert_(ILoops.providedBy(Loops()))
        verifyClass(IConcept, Concept)
        self.assert_(IConcept.providedBy(Concept()))
        verifyClass(IConceptManager, ConceptManager)
        self.assert_(IConceptManager.providedBy(ConceptManager()))


def test_suite():
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                DocFileSuite('README.txt'),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
