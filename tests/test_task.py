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
        self.f1['rsc1'] = self.r1

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


from loops.constraint import ResourceConstraint

class TestTaskResourceConstraints(unittest.TestCase):
    "Test methods of the Task class related to checking for allowed resources."

    def setUp(self):
        self.f1 = Folder()
        self.f1.__name__ = u'f1'
        self.t1 = Task()
        self.r1 = Resource()
        self.f1['tsk1'] = self.t1
        self.r1['rsc1'] = self.r1
        self.rc1 = ResourceConstraint()

    def tearDown(self):
        pass


    # the tests...

    def testSelectExplicit(self):
        t1 = self.t1
        r1 = self.r1
        rc1 = self.rc1

        self.assertEqual(True, t1.isResourceAllowed(r1))    # no check
        self.assertEqual((), t1.getCandidateResources())    # no candidates
        self.assertEqual(None, t1.getAllowedResources([r1]))# can't say without constraint

        self.t1.resourceConstraints.append(self.rc1)        # empty constraint
        self.assertEqual(False, t1.isResourceAllowed(r1))   # does not allow
        self.assertEqual((), t1.getCandidateResources())    # anything
        self.assertEqual((), t1.getAllowedResources([r1]))

        rc1.referenceValues = ([r1])
        self.assertEqual(True, rc1.isResourceAllowed(r1))
        self.assertEqual((r1,), t1.getCandidateResources())
        self.assertEqual((r1,), rc1.getAllowedResources([r1]))


class TestTaskCopy(unittest.TestCase):
    "Tests related to copying tasks e.g. when using task prototypes."

    def setUp(self):
        self.f1 = Folder()
        self.f1.__name__ = u'f1'
        self.t1 = Task()
        self.r1 = Resource()
        self.f1['tsk1'] = self.t1
        self.f1['rsc1'] = self.r1
        self.rc1 = ResourceConstraint()

    def tearDown(self):
        pass


    # the tests...

    def testCopyTask(self):
        t1 = self.t1
        r1 = self.r1
        rc1 = self.rc1
        ts1 = t1.createSubtask()
        ts1.resourceConstraints.append(rc1)
        ts1.allocateResource(r1)
        t2 = t1.copyTask()
        self.failIf(t1 is t2, 't1 and t2 are still the same')
        st2 = t2.getSubtasks()
        self.assertEquals(1, len(st2))
        ts2 = st2[0]
        self.failIf(ts1 is ts2, 'ts1 and ts2 are still the same')
        self.assertEquals((r1,), ts2.getAllocatedResources())
        self.assertEquals([rc1,], ts2.resourceConstraints)


def test_suite():
    return unittest.TestSuite((
#            DocTestSuite('loops.tests.doctests'),
            unittest.makeSuite(TestTask),
            unittest.makeSuite(TestTaskResource),
            unittest.makeSuite(TestTaskResourceConstraints),
            unittest.makeSuite(TestTaskCopy),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
