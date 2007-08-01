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
from twisted.internet.defer import Deferred
from zope.interface import implements

from loops.agent.interfaces import ITransporter, ITransportJob
from loops.agent.schedule import Job


class TransportJob(Job):

    implements(ITransportJob)

    def __init__(self, transporter):
        super(TransportJob, self).__init__()
        self.transporter = transporter

    def execute(self, **kw):
        result = kw.get('result')
        if result is None:
            print 'No data available.'
        else:
            for r in result:
                d = self.transporter.transfer(r[0].data, r[1], str)
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
        config = agent.config

    def transfer(self, resource, metadata=None, resourceType=file):
        if resourceType is file:
            data = resource.read()
            resource.close()
        elif resourceType is str:
            data = resource
        print 'Transferring:', data
        return Deferred()


