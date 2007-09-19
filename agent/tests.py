#! /usr/bin/env python
#
#  Run with ``trial2.4 tests.py`` to execute the twisted unit tests.
#  Run with ``python tests.py`` to execute the doctests.
#

# $Id$

import unittest as standard_unittest
import doctest
import os, time
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.trial import unittest

from loops.agent.schedule import Job
try:
    from loops.agent.core import Agent # needs twisted.internet.task.coiterate
    ignore = False
except ImportError: # wrong environment, skip all loops.agent tests
    print 'Skipping loops.agent'
    ignore = True

baseDir = os.path.dirname(__file__)


class Tester(object):

    def iterate(self, n=10, delays={}):
        for i in range(n):
            delay = delays.get(i, 0)
            reactor.iterate(delay)

tester = Tester()


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
    if ignore:
        return standard_unittest.TestSuite()  # do nothing
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return standard_unittest.TestSuite((
                #standard_unittest.makeSuite(Test),
                doctest.DocFileSuite('README.txt', optionflags=flags),
                doctest.DocFileSuite('crawl/filesystem.txt', optionflags=flags),
                doctest.DocFileSuite('transport/httpput.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    standard_unittest.main(defaultTest='test_suite')
