# $Id$

import unittest
#from zope.testing.doctestunit import DocTestSuite
from zope.interface.verify import verifyClass
#from zope.app.tests.setup import placelessSetUp
#from zope.app.container.tests.test_icontainer import TestSampleContainer
from zope.app.container.interfaces import IContained
from zope.app.folder import Folder

from loops.resource import Resource
from loops.task import Task
from loops.interfaces import IResource

#class Test(TestSampleContainer):
class Test(unittest.TestCase):
    "Test methods of the Resource class."

    def setUp(self):
        #placelessSetUp()
        self.f1 = Folder()
        self.f1.__name__ = u'f1'
        self.r1 = Resource()
        self.f1['rsc1'] = self.r1
        self.t1 = Task()
        self.f1['tsk1'] = self.t1

    def tearDown(self):
        pass

    # the tests...

    def testInterface(self):
        self.assert_(IResource.providedBy(Resource()),
            'Interface IResource is not implemented by class Resource.')
        self.assert_(IContained.providedBy(Resource()),
            'Interface IContained is not implemented by class Resource.')
        verifyClass(IResource, Resource)

    def testContained(self):
        self.assertEqual(u'rsc1', self.r1.__name__)
        self.assertEqual(u'f1', self.r1.__parent__.__name__)

    def testTitle(self):
        r = Resource()
        self.assertEqual(u'', r.title)
        r.title = u'First Resource'
        self.assertEqual(u'First Resource', r.title)

    def testAllocateToTask(self):
        t1 = self.t1
        r1 = self.r1
        self.assertEqual((), r1.getTasksAllocatedTo())
        t1.allocateResource(r1)
        self.assertEqual((t1,), r1.getTasksAllocatedTo())


def test_suite():
    return unittest.TestSuite((
#            DocTestSuite('loops.tests.doctests'),
            unittest.makeSuite(Test),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
