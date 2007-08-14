#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Job scheduling.

$Id$
"""

from time import time
from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed
from zope.interface import implements

from loops.agent.interfaces import IScheduler, IScheduledJob


class Scheduler(object):

    implements(IScheduler)

    def __init__(self, agent):
        self.agent = agent
        self.queue = {}
        self.logger = None

    def schedule(self, job, startTime=None):
        if startTime is None:
            startTime = int(time())
        job.startTime = startTime
        job.scheduler = self
        while startTime in self.queue:
            startTime += 1
        self.queue[startTime] = job
        reactor.callLater(startTime-int(time()), job.run)

    def getJobsToExecute(startTime=None):
        return [j for j in self.queue.values() if (startTime or 0) <= j.startTime]


class Job(object):

    implements(IScheduledJob)

    scheduler = None

    whenStarted = lambda self: None
    whenFinished = lambda self, result: None

    def __init__(self, **params):
        self.startTime = 0
        self.params = params
        self.successors = []
        self.repeat = 0

    def execute(self):
        """ Must be overridden by subclass.
        """
        return succeed('OK')

    def reschedule(self, startTime):
        self.scheduler.schedule(self.copy(), startTime)

    def run(self):
        d = self.execute()
        d.addCallback(self.finishRun)
        self.whenStarted()
        # TODO: logging

    def finishRun(self, result):
        # remove from queue
        del self.scheduler.queue[self.startTime]
        # run successors
        for job in self.successors:
            job.params['result'] = result
            #job.run()
            self.scheduler.schedule(job)
        self.whenFinished(result)
        # TODO: logging
        # reschedule if necessary
        if self.repeat:
            self.reschedule(int(time() + self.repeat))

    def copy(self):
        newJob = Job()
        newJob.params = self.params
        newJob.successors = [s.copy() for s in self.successors]


class Stopper(Job):

    def execute(self):
        reactor.stop()
        return succeed('Agent stopped.')

