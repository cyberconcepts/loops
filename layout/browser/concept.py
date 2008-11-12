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
Layout-based concept views.

$Id$
"""

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.traversing.browser import absoluteURL

from cybertools.composer.layout.browser.view import Page
from loops.browser.common import BaseView
from loops.common import adapted
from loops.i18n.browser import LanguageInfo
from loops.interfaces import IConcept
from loops.layout.interfaces import ILayoutNode
from loops.versioning.util import getVersion
from loops import util


class ConceptView(object):

    node = None

    def __init__(self, context, request):
        self.context = context  # this is the adapted concept!
        self.request = request

    @Lazy
    def title(self):
        return self.context.title

    @Lazy
    def url(self):
        return '%s/.%s' % (absoluteURL(self.node, self.request), self.context.uid)

    @property
    def children(self):
        for c in self.context.getChildren():
            view = component.getMultiAdapter((c, self.request), name='layout')
            view.node = self.node
            yield view

