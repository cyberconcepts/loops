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
        self.rc1 = ResourceConstraint()

    def tearDown(self):
        pass

    # the tests...

    def testInterface(self):
        self.failUnless(IResourceConstraint.providedBy(self.rc1),
            'Interface IResourceConstraint is not implemented by class ResourceConstraint.')
        verifyClass(IResourceConstraint, ResourceConstraint)

    def testRequireExplicit(self):
        rc1 = self.rc1
        r1 = self.r1
        self.assertEqual(False, rc1.isResourceAllowed(r1))
        self.assertEqual((), rc1.getAllowedResources())
        rc1.referenceValues = ([r1])
        self.assertEqual(True, rc1.isResourceAllowed(r1))
        self.assertEqual((r1,), rc1.getAllowedResources())

    def testRequireParent(self):
        rc1 = self.rc1
        r1 = self.r1
        t2 = Task()
        t2.allocateResource(r1)
        rc1.referenceType = 'parent'
        rc1.referenceKey = 'getAllocatedResources'
        rc1.referenceValues = ([t2])
        self.assertEqual(True, rc1.isResourceAllowed(r1))
        self.assertEqual((r1,), rc1.getAllowedResources())
        rc1.referenceType = 'parent'
        rc1.referenceKey = 'getAllocatedResources'

    def testRequireCheckmethod(self):
        rc1 = self.rc1
        rc1.referenceType = 'checkmethod'
        rc1.referenceKey = 'isAllowedForTesting'
        r1 = self.r1
        t1 = self.t1
        self.failIf(rc1.isResourceAllowed(r1))
        Resource.isAllowedForTesting = lambda self: True
        self.failUnless(rc1.isResourceAllowed(r1))
        Resource.isAllowedForTesting = lambda self: False
        self.failIf(rc1.isResourceAllowed(r1, t1))

    def testRequireSelectMethod(self):
        rc1 = self.rc1
        rc1.referenceType = 'selectmethod'
        rc1.referenceKey = 'selectResources'
        r1 = self.r1
        t1 = self.t1
        def method(self, candidates, task):
            if task is None: return None
            return (r1,)
        ResourceConstraint.selectResources = method
        self.assertEqual((r1,), rc1.getAllowedResources(task=t1))
        self.failUnless(rc1.isResourceAllowed(r1, task=t1))



def test_suite():
    return unittest.TestSuite((
#            DocTestSuite('loops.tests.doctests'),
            unittest.makeSuite(Test),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
