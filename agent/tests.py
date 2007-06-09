# $Id$

import unittest as standard_unittest
import doctest
import time
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.trial import unittest

from loops.agent.core import Agent
from loops.agent.schedule import Job


class TestJob(Job):

    def execute(self, deferred, **kw):
        d = super(TestJob, self).execute(**kw)
        #print 'executing'
        deferred.callback('Done')
        return d


class Test(unittest.TestCase):
    "Basic tests for the loops.agent package."

    def setUp(self):
        self.agent = Agent()

    def tearDown(self):
        pass

    def testScheduling(self):
        d = Deferred()
        job = TestJob()
        job.params['deferred'] = d
        w = self.agent.scheduler.schedule(job, int(time.time())+1)
        return d


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return standard_unittest.TestSuite((
                standard_unittest.makeSuite(Test),
                doctest.DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
