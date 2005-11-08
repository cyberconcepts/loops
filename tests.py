# $Id$

import unittest
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass
from zope.interface import implements
from zope.app import zapi
from zope.app.intid.interfaces import IIntIds

from interfaces import ITask
from task import Task

class Test(unittest.TestCase):
    "Basic tests for the loops package."

    def testInterfaces(self):
        verifyClass(ITask, Task)
        self.assert_(ITask.providedBy(Task()),
            'Interface ITask is not implemented by class Task.')


def test_suite():
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                DocFileSuite('README.txt'),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
