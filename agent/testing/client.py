#! /usr/bin/env python
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
A dummy client application for testing purposes.

Run this from above the loops directory with::

  python loops/agent/testing/client.py

$Id$
"""

import os
import sys
from time import time
from twisted.internet import reactor

from loops.agent.core import Agent
from loops.agent.crawl.filesystem import CrawlingJob
from loops.agent.transport.base import Transporter
from loops.agent.tests import baseDir

if len(sys.argv) > 1:
    cfgName = sys.argv[1]
else:
    cfgName = os.path.join(baseDir, 'testing', 'testing.cfg')
cfg = open(cfgName)

agent = Agent(cfg.read())
agent.scheduleJobsFromConfig(stop=True)

print 'Starting reactor.'

reactor.run()

print 'Reactor stopped.'
