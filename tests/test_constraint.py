# $Id$

import unittest
#from zope.testing.doctestunit import DocTestSuite
from zope.interface.verify import verifyClass
from zope.app.container.interfaces import IContained
from zope.app.folder import Folder

from loops.task import Task
from loops.resource import Resource
from loops.constraint import ResourceConstraint
from loops.interfaces import IResourceConstraint

class Test(unittest.TestCase):
    "Test methods of the ResourceConstraint class."

    def setUp(self):
        #placelessSetUp()
        self.f1 = Folder()
        self.f1.__name__ = u'f1'
        self.r1 = Resource()
        self.f1['rsc1'] = self.r1
        self.t1 = Task()
        self.f1['tsk1'] = self.t1
        self.rc1 = ResourceConstraint(self.t1)

    def tearDown(self):
        pass

    # the tests...

    def testInterface(self):
        self.failUnless(IResourceConstraint.providedBy(self.rc1),
            'Interface IResourceConstraint is not implemented by class ResourceConstraint.')
        verifyClass(IResourceConstraint, ResourceConstraint)

    def testSelectExplicit(self):
        rc1 = self.rc1
        r1 = self.r1
        self.assertEqual(False, rc1.isResourceAllowed(r1))
        self.assertEqual((), rc1.getAllowedResources())
        rc1.referenceValues = ([r1])
        self.assertEqual(True, rc1.isResourceAllowed(r1))
        self.assertEqual((r1,), rc1.getAllowedResources())

    def testSelectParent(self):
        rc1 = self.rc1
        r1 = self.r1
        t2 = Task()
        t2.allocateResource(r1)
        rc1.referenceType = 'parent'
        rc1.referenceKey = 'getAllocatedResources'
        rc1.referenceValues = ([t2])
        self.assertEqual(True, rc1.isResourceAllowed(r1))
        self.assertEqual((r1,), rc1.getAllowedResources())


def test_suite():
    return unittest.TestSuite((
#            DocTestSuite('loops.tests.doctests'),
            unittest.makeSuite(Test),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
