#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
"""

from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.security.proxy import removeSecurityProxy

from cybertools.composer.layout.browser.view import Page
from loops.common import adapted
from loops.layout.browser.base import BaseView


class LayoutNodeView(Page, BaseView):

    def __init__(self, context, request):
        super(LayoutNodeView, self).__init__(context, request)
        #Page.__init__(self, context, request)
        self.viewAnnotations.setdefault('node', removeSecurityProxy(context))

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

    @Lazy
    def target(self):
        target = self.viewAnnotations.get('target')
        if target is None:
            target = adapted(self.context.target)
        return target

    @Lazy
    def headTitle(self):
        parts = [self.context.title]
        if self.target is not None:
            targetView = component.getMultiAdapter((self.target, self.request),
                                                   name='layout')
            title = getattr(targetView, 'headTitle', targetView.title)
            if title not in parts:
                parts.append(title)
        if self.globalOptions('reverseHeadTitle'):
            parts.reverse()
        return ' - '.join(parts)
