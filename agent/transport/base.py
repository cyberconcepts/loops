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
Transporter base classes.

$Id$
"""

from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList, fail
from zope.interface import implements

from loops.agent.interfaces import ITransporter, ITransportJob
from loops.agent.schedule import Job


class TransportJob(Job):

    implements(ITransportJob)

    def __init__(self, transporter):
        super(TransportJob, self).__init__()
        self.transporter = transporter

    def execute(self):
        result = self.params.get('result')
        if result is None:
            return fail('No data available.')
        transfers = []
        for resource in result:
            d = self.transporter.transfer(resource)
            transfers.append(d)
            d.addCallback(self.logTransfer)
        return DeferredList(transfers)

    def logTransfer(self, result):
        # TODO: logging
        # self.transporter.agent.logger.log(...)
        pass


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

    def createJob(self):
        return self.jobFactory(self)

    def transfer(self, resource):
        data = resource.data
        if type(data) is file:
            text = resource.read()
            resource.close()
        else:
            text = data
        path = resource.path
        app = resource.application
        deferreds = []
        metadata = resource.metadata
        if metadata is not None:
            url = self.makePath('meta', app, path)
            deferreds.append(
                    getPage(url, method=self.method, postData=metadata.asXML()))
        url = self.makePath('data', app, path)
        deferreds.append(getPage(url, method=self.method, postData=text))
        return DeferredList(deferreds)

    def makePath(self, infoType, app, path):
        return '/'.join((self.serverURL, infoType, app, path))

