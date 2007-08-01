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
A dummy crawler for testing purposes.

$Id$
"""

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from zope.interface import implements

from loops.agent.interfaces import ICrawlingJob, IResource, IMetadataSet
from loops.agent.crawl.base import CrawlingJob as BaseCrawlingJob


class CrawlingJob(BaseCrawlingJob):

    def collect(self, **criteria):
        deferred = self.deferred = Deferred()
        # replace this with the real stuff:
        reactor.callLater(0, self.dataAvailable)
        return deferred

    def dataAvailable(self):
        self.deferred.callback([(DummyResource(), Metadata())])


class Metadata(object):

    implements(IMetadataSet)


class DummyResource(object):

    implements(IResource)

    data = 'Dummy resource data for testing purposes.'
