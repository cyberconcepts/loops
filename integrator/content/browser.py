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
View class(es) for accessing external objects.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.publisher.browser import getDefaultViewName
from zope.cachedescriptors.property import Lazy

from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.common import adapted


view_macros = ViewPageTemplateFile('view_macros.pt')


class ExternalAccessRenderer(NodeView):

    @Lazy
    def adapted(self):
        return adapted(self.virtualTargetObject)

    def __call__(self):
        obj = self.adapted()
        name = getDefaultViewName(obj, self.request)
        view = component.getMultiAdapter((obj, self.request), name=name)
        return view()

    def publishTraverse(self, request, name):
        return self.adapted()[name]


class FlashVideo(ConceptView):

    @Lazy
    def macro(self):
        return view_macros.macros['flashvideo']

    @Lazy
    def startName(self):
        return self.adapted.address + '.html'
