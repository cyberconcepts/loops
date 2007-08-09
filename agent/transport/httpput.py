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
Transferring of data/files to the server.

$Id$
"""

from twisted.internet import reactor
from twisted.web.client import getPage
from zope.interface import implements

from loops.agent.interfaces import ITransporter, ITransportJob
from loops.agent.schedule import Job


class TransportJob(Job):

    implements(ITransportJob)

    def __init__(self, transporter):
        super(TransportJob, self).__init__()
        self.transporter = transporter

    def execute(self):
        result = kw.get('result')
        if result is None:
            print 'No data available.'
        else:
            for resource, metadata in result:
                d = self.transporter.transfer(resource.data, metadata)
        return Deferred()


class Transporter(object):

    implements(ITransporter)

    jobFactory = TransportJob

    serverURL = None
    method = None
    machineName = None
    userName = None
    password = None

    def __init__(self, agent):
        self.agent = agent
        conf = agent.config
        # TODO: get settings from conf

    def transfer(self, resource):
        data = resource.data
        if type(data) is file:
            text = resource.read()
            resource.close()
        else:
            text = data
        metadata = resource.metadata
        url = self.serverURL + self.makePath(metadata)
        d = getPage(url, method='PUT', postData=text)
        return d

