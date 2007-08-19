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
Log information management.

$Id$
"""

import logging
import sys
import time
from zope.interface import implements

from loops.agent.interfaces import ILogger, ILogRecord


class LogRecord(object):

    implements(ILogRecord)

    datefmt = '%Y-%m-%dT%H:%S'

    def __init__(self, logger, data):
        self.logger = logger
        self.data = data
        self.timeStamp = time.time()

    def __str__(self):
        msg = [str(time.strftime(self.datefmt, time.localtime(self.timeStamp)))]
        for k in sorted(self.data):
            msg.append('%s:%s' % (str(k), str(self.data[k])))
        return ' '.join(msg)


class Logger(list):

    implements(ILogger)

    recordFactory = LogRecord


    def __init__(self, agent):
        self.agent = agent
        self.setup()

    def setup(self):
        self.externalLoggers = []
        conf = self.agent.config.logging
        if conf.standard:
            logger = logging.getLogger()
            logger.level = conf.standard
            logger.addHandler(logging.StreamHandler(sys.stdout))
            self.externalLoggers.append(logger)

    def log(self, data):
        record = self.recordFactory(self, data)
        self.append(record)
        for logger in self.externalLoggers:
            logger.info(str(record))

