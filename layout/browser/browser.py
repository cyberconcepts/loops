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

from zope import component
from zope.app.container.traversal import ItemTraverser
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements
from zope.traversing.browser import absoluteURL

from cybertools.composer.layout.browser.view import Page
from loops.browser.common import BaseView
from loops.common import adapted
from loops.i18n.browser import LanguageInfo
from loops.interfaces import IConcept
from loops.layout.interfaces import ILayoutNode
from loops.versioning.util import getVersion
from loops import util


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

    node = None

    def __init__(self, context, request):
        if IConcept.providedBy(context):
            self.adapted = adapted(context)
            self.context = context
        else:
            self.adapted = context
            self.context = context.context
        self.request = request

    @Lazy
    def title(self):
        return self.context.title

    @Lazy
    def url(self):
        return '%s/.%s' % (absoluteURL(self.node, self.request),
                                 util.getUidForObject(self.context))

    @property
    def children(self):
        for c in self.context.getChildren():
            view = component.getMultiAdapter((adapted(c), self.request), name='layout')
            view.node = self.node
            yield view


class NodeTraverser(ItemTraverser):

    adapts(ILayoutNode)

    def publishTraverse(self, request, name):
        if name.startswith('.'):
            if len(name) > 1:
                uid = int(name[1:])
                target = util.getObjectForUid(uid)
            else:
                target = self.context.target
            if target is not None:
                viewAnnotations = request.annotations.setdefault('loops.view', {})
                viewAnnotations['node'] = self.context
                target = getVersion(target, request)
                target = adapted(target, LanguageInfo(target, request))
                viewAnnotations['target'] = target
                return target
                #return self.context
        obj = super(NodeTraverser, self).publishTraverse(request, name)
        return obj
