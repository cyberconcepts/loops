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

from zope.interface import implements

from loops.agent.interfaces import ICrawlingJob, IMetadataSet
from loops.agent.schedule import Job


class CrawlingJob(Job):

    implements(ICrawlingJob)

    baseProperties = ('starttime', 'type', 'repeat', 'transportType',)

    def __init__(self, **params):
        self.predefinedMetadata = {}
        super(CrawlingJob, self).__init__(**params)

    def execute(self):
        return self.collect()


class Metadata(dict):

    implements(IMetadataSet)

    def __init__(self, data=dict()):
        for k in data:
            self[k] = data[k]

    def asXML(self):
        # TODO...
        return ''

    def set(self, key, value):
        self['key'] = value

