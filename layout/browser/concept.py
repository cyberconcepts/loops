#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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

import re

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.proxy import removeAllProxies
from zope.traversing.browser import absoluteURL

from loops.common import adapted
from loops.i18n.browser import LanguageInfo
from loops.interfaces import IConcept
from loops.layout.browser.base import BaseView
from loops import util


class ConceptView(BaseView):

    @property
    def children(self):
        for c in self.context.getChildren():
        #for c in self.context.getChildren([self.defaultPredicate]):
            a = adapted(c)
            #view = component.getMultiAdapter((c, self.request), name='layout')
            view = component.getMultiAdapter((a, self.request), name='layout')
            view.node = self.node
            yield view

