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
A dummy webserver for testing the loops.agent HTTP transport.

Run this with::

    twistd -noy loops/agent/testing/server.py

$Id$
"""

from twisted.application import service, internet
from twisted.web import http


class RequestHandler(http.Request):

    def process(self):
        print '***', repr(self.content.read())
        if self.method in ('GET', 'POST'):
            self.write('<h1>Hello World</h1>')
            self.write('<p>dir(self): %s</p>' % dir(self))
            self.write('<p>self.path: %s</p>' % self.path)
            self.write('<p>self.uri: %s</p>' % self.uri)
            self.write('<p>self.args: %s</p>' % self.args)
        self.finish()


class HttpServer(http.HTTPChannel):

    requestFactory = RequestHandler


class HttpFactory(http.HTTPFactory):

    protocol = HttpServer


class HttpService(internet.TCPServer):

    def __init__(self):
        internet.TCPServer.__init__(self, 8123, HttpFactory())


application = service.Application('Simple Webserver')
HttpService().setServiceParent(application)
