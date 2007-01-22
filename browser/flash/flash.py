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
View class(es) for Flash user interface.

$Id$
"""

from zope.app.traversing.browser.absoluteurl import absoluteURL
from zope.cachedescriptors.property import Lazy


class FlashView(object):
    """
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def setHeaders(self):
        response = self.request.response
        response.setHeader('Content-Type', 'text/html;charset=utf-8')
        response.setHeader('Expires', 'Sat, 1 Jan 2000 00:00:00 GMT');
        response.setHeader('Pragma', 'no-cache');

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    #@Lazy
    def loopsUrl(self):
        return absoluteURL(self.loopsRoot, self.request)

