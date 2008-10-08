#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Layout node views.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.traversing.browser import absoluteURL

from cybertools.composer.layout.browser.view import Page
from loops.browser.common import BaseView


class LayoutNodeView(Page):

    @Lazy
    def layoutName(self):
        return self.context.viewName or 'page'

    @Lazy
    def layoutNames(self):
        result = []
        n = self.context
        while n is not None:
            if n.viewName:
                result.append(n.viewName)
            n = n.getParentNode()
        result.append('page')
        return result


class ConceptView(object):

    def __init__(self, context, request, node=None):
        self.context = context
        self.request = request
        self.node = node

    @Lazy
    def title(self):
        return self.context.title

    @Lazy
    def url(self):
        return absoluteURL(self.node, self.request)

    @property
    def children(self):
        for c in self.context.getChildren():
            yield ConceptView(c, self.request, self.node)

