# $Id$

import unittest, doctest
import time
from twisted.internet import reactor

from loops.agent.core import Agent
from loops.agent.schedule import Job


class TestJob(Job):

    def execute(self, **kw):
        d = super(TestJob, self).execute(**kw)
        print 'executing'
        return d


class Test(unittest.TestCase):
    "Basic tests for the loops.agent package."

    def setUp(self):
        self.agent = Agent()

    def testScheduling(self):
        d = self.agent.scheduler.schedule(TestJob(), int(time.time())+1)
        time.sleep(1)


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                doctest.DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
