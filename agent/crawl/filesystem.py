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
Filesystem crawler.

$Id$
"""

import os
from fnmatch import filter
from datetime import datetime
from twisted.internet.defer import Deferred
from twisted.internet.task import coiterate
from zope.interface import implements

from loops.agent.interfaces import IResource
from loops.agent.crawl.base import CrawlingJob as BaseCrawlingJob
from loops.agent.crawl.base import Metadata


class CrawlingJob(BaseCrawlingJob):

    def collect(self):
        self.collected = []
        coiterate(self.crawlFilesystem()).addCallback(self.finished)
        # TODO: addErrback()
        self.deferred = Deferred()
        return self.deferred

    def finished(self, result):
        self.deferred.callback(self.collected)

    def crawlFilesystem(self):
        directory = self.params.get('directory')
        pattern = self.params.get('pattern') or '*'
        lastRun = self.params.get('lastrun') or datetime(1980, 1, 1)
        for path, dirs, files in os.walk(directory):
            if '.svn' in dirs:
                del dirs[dirs.index('.svn')]
            for f in filter(files, pattern):
                filename = os.path.join(path, f)
                mtime = datetime.fromtimestamp(os.path.getmtime(filename))
                if mtime <= lastRun:  # file not changed
                    continue
                meta = dict(
                    path=filename,
                )
                self.collected.append(FileResource(filename, Metadata(meta)))
                yield None


class FileResource(object):

    implements(IResource)

    def __init__(self, path, metadata=None):
        self.path = path
        self.metadata = metadata

    @property
    def data(self):
        return open(self.path, 'r')

