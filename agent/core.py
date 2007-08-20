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
The real agent stuff.

$Id$
"""

from time import time
from zope.interface import implements
from loops.agent.interfaces import IAgent
from loops.agent.config import Configurator
from loops.agent.crawl import filesystem
from loops.agent.log import Logger
from loops.agent.schedule import Scheduler, Stopper
from loops.agent.transport import base


crawlTypes = dict(
        filesystem=filesystem.CrawlingJob,
)

transportTypes = dict(
        httpput=base.Transporter,
)


class Agent(object):

    implements(IAgent)

    crawlTypes = crawlTypes
    transportTypes = transportTypes

    def __init__(self, conf=None):
        config = self.config = Configurator('ui', 'crawl', 'transport', 'logging')
        config.load(conf)
        self.scheduler = Scheduler(self)
        self.stopper = Stopper()
        self.stopper.scheduler = self.scheduler
        self.logger = Logger(self)

    def scheduleJobsFromConfig(self, stop=False):
        config = self.config
        scheduler = self.scheduler
        lastJob = None
        for idx, info in enumerate(config.crawl):
            crawlType = info.type
            factory = self.crawlTypes.get(crawlType)
            if factory is not None:
                job = lastJob = factory()
                job.params = dict((name, value)
                                for name, value in info.items()
                                if name not in job.baseProperties)
                transportType = info.transport or 'httpput'
                factory = self.transportTypes.get(transportType)
                if factory is not None:
                    params = dict(config.transport.items())
                    transporter = factory(self, **params)
                    # TODO: configure transporter or - better -
                    #       set up transporter(s) just once
                    job.successors.append(transporter.createJob())
                job.repeat = info.repeat or 0
                self.scheduler.schedule(job, info.starttime or int(time()))
                # TODO: remove job from config
                # TODO: put repeating info in config
                # TODO: remember last run for repeating job
        if stop:
            if lastJob is not None:
                lastTrJob = lastJob.successors[-1]
                lastTrJob.successors.append(self.stopper)
            else:
                self.scheduler.schedule(self.stopper)

