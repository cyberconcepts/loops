# $Id$

import unittest
#from zope.testing.doctestunit import DocTestSuite
from zope.interface.verify import verifyClass
#from zope.app.tests.setup import placelessSetUp
from zope.app.tests.setup import placefulSetUp
#from zope.app.container.tests.test_icontainer import TestSampleContainer
from zope.app.container.interfaces import IContained
from zope.app.folder import Folder
from zope.app import zapi

from loops.task import Task
from loops.interfaces import ITask

#class Test(TestSampleContainer):
class TestTask(unittest.TestCase):
    "Test methods of the Task class."

    def setUp(self):
#        placelessSetUp()
        placefulSetUp()
        self.f1 = Folder()
        self.f1.__name__ = u'f1'
        self.t1 = Task()
        self.f1['tsk1'] = self.t1

    def tearDown(self):
        pass

    # the tests...

    def testInterface(self):
        self.assert_(ITask.providedBy(Task()),
            'Interface ITask is not implemented by class Task.')
        self.assert_(IContained.providedBy(Task()),
            'Interface IContained is not implemented by class Task.')
        verifyClass(ITask, Task)

    def testContained(self):
        self.assertEqual(u'tsk1', zapi.name(self.t1))
        self.assertEqual(u'f1', zapi.name(zapi.getParent(self.t1)))

    def testTitle(self):
        t = Task()
        self.assertEqual(u'', t.title)
        t.title = u'First Task'
        self.assertEqual(u'First Task', t.title)

    def testSubtasks(self):
        t1 = Task()
        self.assertEqual((), t1.getSubtasks())
        t2 = Task()
        self.assertEqual((), t2.getSubtasks())
        self.assertEqual((), t2.getParentTasks())
        t1.assignSubtask(t2)
        self.assertEqual((t2,), t1.getSubtasks())
        self.assertEqual((t1,), t2.getParentTasks())

    def testCreateSubtask(self):
        t1 = self.t1
        self.assertEqual((), t1.getSubtasks())
        t2 = t1.createSubtask()
        self.assertEqual((t1,), t2.getParentTasks())
        self.assertEqual((t2,), t1.getSubtasks())

    def testDeassignSubtask(self):
        t1 = self.t1
        t2 = t1.createSubtask()
        self.assertEqual((t1,), t2.getParentTasks())
        t1.deassignSubtask(t2)
        self.assertEqual((), t2.getParentTasks())
        self.assertEqual((), t1.getSubtasks())


from loops.resource import Resource

class TestTaskResource(unittest.TestCase):
    "Test methods of the Task class related to Resource allocations."

    def setUp(self):
        #placelessSetUp()
        #placefulSetUp()
        self.f1 = Folder()
        self.f1.__name__ = u'f1'
        self.t1 = Task()
        self.r1 = Resource()
        self.f1['tsk1'] = self.t1
        self.r1['rsc1'] = self.r1

    def tearDown(self):
        pass

    # the tests...

    def testAllocateResource(self):
        t1 = self.t1
        r1 = self.r1
        self.assertEqual((), t1.getAllocatedResources())
        t1.allocateResource(r1)
        self.assertEqual((r1,), t1.getAllocatedResources())

    def testDeallocateResource(self):
        t1 = self.t1
        r1 = self.r1
        t1.allocateResource(r1)
        self.assertEqual((r1,), t1.getAllocatedResources())
        t1.deallocateResource(r1)
        self.assertEqual((), t1.getAllocatedResources())

    def testCreateAndAllocateResource(self):
        t1 = self.t1
        self.assertEqual((), t1.getAllocatedResources())
        r1 = t1.createAndAllocateResource()
        self.assertEqual((r1,), t1.getAllocatedResources())


def test_suite():
    return unittest.TestSuite((
#            DocTestSuite('loops.tests.doctests'),
            unittest.makeSuite(TestTask),
            unittest.makeSuite(TestTaskResource),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
