# $Id$

import unittest
from zope.testing.doctestunit import DocTestSuite
from zope.app.container.tests.test_icontainer import TestSampleContainer
from zope.interface.verify import verifyClass

from src.loops.task import Task
from src.loops.interfaces import ITask

#class Test(TestSampleContainer):
class Test(unittest.TestCase):
    "Test methods of the Task class."

    def testInterface(self):
        self.assert_(ITask.providedBy(Task()), 'Interface ITask is not implemented by class Task.')
        verifyClass(ITask, Task)

    def testTitle(self):
        t = Task()
        self.assertEqual(u'', t.title)
        t.title = u'First Task'
        self.assertEqual(u'First Task', t.title)

    def testSubtasks(self):
        t1 = Task()
        self.assertEquals((), t1.getSubtasks())
        t2 = Task()
        self.assertEquals((), t2.getSubtasks())
        self.assertEquals((), t2.getParentTasks())
        t1.assignSubtask(t2)
        self.assertEquals((t2,), t1.getSubtasks())
        self.assertEquals((t1,), t2.getParentTasks())

def test_suite():
    return unittest.TestSuite((
            #DocTestSuite('src.loops.task'),
            unittest.makeSuite(Test),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
