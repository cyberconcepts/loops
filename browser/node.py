#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
View class for Node objects.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.app import zapi
from zope.app.container.browser.contents import JustContents
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.proxy import removeAllProxies
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy


class NodeView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def render(self, text=None):
        if text is None:
            text = self.context.body
        if not text:
            return u''
        if text.startswith('<'):  # seems to be HTML
            return text
        source = zapi.createObject(self.context.contentType, text)
        view = zapi.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()

    @Lazy
    def modified(self):
        """ get date/time of last modification
        """
        dc = ICMFDublinCore(self.context)
        d = dc.modified or dc.created
        return d and d.strftime('%Y-%m-%d %H:%M') or ''

    @Lazy
    def target(self):
        return self.context.target

    @Lazy
    def page(self):
        page = self.context.getPage()
        return page is not None and NodeView(page, self.request) or None

    def textItems(self):
        for child in self.context.getTextItems():
            yield NodeView(child, self.request)

    @Lazy
    def menu(self):
        menu = self.context.getMenu()
        return menu is not None and NodeView(menu, self.request) or None

    def menuItems(self):
        for child in self.context.getMenuItems():
            yield NodeView(child, self.request)

    @Lazy
    def body(self):
        return self.render()

    @Lazy
    def url(self):
        return zapi.absoluteURL(self.context, self.request)

    @Lazy
    def editable(self):
        return canWrite(self.context, 'body')

    def selected(self, item):
        return item.context == self.context


class OrderedContainerView(JustContents):
    """ A view providing the necessary methods for moving sub-objects
        within an ordered container.
    """

    @Lazy
    def url(self):
        return zapi.absoluteURL(self.context, self.request)

    @Lazy
    def orderable(self):
        return len(self.context) > 1

    def checkMoveAction(self):
        request = self.request
        for var in request:
            if var.startswith('move_'):
                params = []
                if 'delta' in request:
                    params.append('delta=' + request['delta'])
                if 'ids' in request:
                    for id in request['ids']:
                        params.append('ids:list=' + id)
                request.response.redirect('%s/%s?%s'
                                          % (self.url, var, '&'.join(params)))
                return True
        return False

    def moveDown(self, ids=[], delta=1):
        self.context.moveSubNodesByDelta(ids, int(delta))
        self.request.response.redirect(self.url + '/contents.html')

    def moveUp(self, ids=[], delta=1):
        self.context.moveSubNodesByDelta(ids, -int(delta))
        self.request.response.redirect(self.url + '/contents.html')

    def moveToBottom(self, ids=[]):
        self.context.moveSubNodesByDelta(ids, len(self.context))
        self.request.response.redirect(self.url + '/contents.html')

    def moveToTop(self, ids=[]):
        self.context.moveSubNodesByDelta(ids, -len(self.context))
        self.request.response.redirect(self.url + '/contents.html')


