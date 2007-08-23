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

from base64 import b64encode
from twisted.internet import reactor
from twisted.internet.defer import Deferred, fail
from twisted.web.client import getPage
from zope.interface import implements

from loops.agent.interfaces import ITransporter, ITransportJob
from loops.agent.schedule import Job


class TransportJob(Job):

    implements(ITransportJob)

    def __init__(self, transporter):
        super(TransportJob, self).__init__()
        self.transporter = transporter
        self.resources = []
        self.deferred = None

    def execute(self):
        result = self.params.get('result')
        if result is None:
            return fail('No data available.')
        self.resources = result
        self.deferred = Deferred()
        d = self.transporter.transfer(self.resources.pop())
        d.addCallback(self.transferDone).addErrback(self.logError)
        return self.deferred

    def transferDone(self, result):
        self.logTransfer(result)
        if self.resources:
            d = self.transporter.transfer(self.resources.pop())
            d.addCallback(self.transferDone).addErrback(self.logError)
        else:
            self.deferred.callback('OK')

    def logTransfer(self, result, err=None):
        #print 'transfer successful; remaining:', len(self.resources)
        # TODO: logging
        # self.transporter.agent.logger.log(...)
        pass

    def logError(self, error):
        print '*** error on transfer', self.transporter.serverURL, error
        self.deferred.errback(error)


class Transporter(object):

    implements(ITransporter)

    jobFactory = TransportJob

    serverURL = 'http://localhost:8080'
    method = 'PUT'
    machineName = 'unknown'
    userName = 'nobody'
    password = 'secret'

    def __init__(self, agent, **params):
        self.agent = agent
        for k, v in params.items():
            setattr(self, k ,v)
        self.deferred = None

    def createJob(self):
        return self.jobFactory(self)

    def transfer(self, resource):
        data = resource.data
        if type(data) is file:
            text = data.read()
            data.close()
        else:
            text = data
        path = resource.path
        app = resource.application
        metadata = resource.metadata
        auth = b64encode(self.userName + ':' + self.password)
        headers = {'Authorization': 'Basic ' + auth}
        url = self.makePath('.data', app, path)
        d = getPage(url, method=self.method, headers=headers, postdata=text)
        if metadata is None:
            d.addCallback(self.finished)
        else:
            d.addCallback(self.transferMeta, app, path, headers, metadata.asXML())
        self.deferred = Deferred()
        return self.deferred

    def transferMeta(self, result, app, path, headers, text):
        url = self.makePath('.meta', app, path)
        d = getPage(url, method=self.method, headers=headers, postdata=text)
        d.addCallback(self.finished)

    def finished(self, result):
        self.deferred.callback(result)

    def makePath(self, infoType, app, path, extension=None):
        if path.startswith('/'):
            path = path[1:]
        url = self.serverURL
        if url.endswith('/'):
            url = url[:-1]
        fullPath = '/'.join((url, infoType,
                             self.machineName, self.userName, app, path))
        if extension:
            fullPath += '.' + extension
        return fullPath

