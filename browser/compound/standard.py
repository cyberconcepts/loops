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
Definition of compound views.
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from loops.browser.concept import ConceptView
from loops.util import _


compound_macros = ViewPageTemplateFile('view_macros.pt')


class CompoundView(ConceptView):

    @Lazy
    def macro(self):
        return compound_macros.macros['standard']

    def getParts(self):
        parts = (self.options('view_parts') or self.typeOptions('view_parts') or [])
        return self.getPartViews(parts)

    def getPartViews(self, parts):
        result = []
        for p in parts:
            view = component.queryMultiAdapter((self.adapted, self.request), name=p)
            if view is None:
                view = component.queryMultiAdapter((self.context, self.request), name=p)
                if view is not None:
                    view.parent = self
                    result.append(view)
        return result

