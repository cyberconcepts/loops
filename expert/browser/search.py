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
Definition of basic view classes and other browser related stuff for the
loops.expert package.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName, getParent

from loops.browser.node import NodeView
from loops.expert.concept import ConceptQuery, FullQuery
from loops.organize.personal.browser.filter import FilterView
from loops import util
from loops.util import _


searchMacrosTemplate = ViewPageTemplateFile('search.pt')


class SearchResults(NodeView):
    """ Provides results listing """

    @Lazy
    def search_macros(self):
        return self.controller.getTemplateMacros('search', searchMacrosTemplate)

    @Lazy
    def macro(self):
        return self.search_macros['quicksearch_view']

    @Lazy
    def item(self):
        return self

    @Lazy
    def results(self):
        form = self.request.form
        text = form.get('search.text')
        type = self.globalOptions('expert.quicksearch')
        result = FullQuery(self).query(text=text, type=type,
                           useTitle=True, useFull=True,)
        fv = FilterView(self.context, self.request)
        result = fv.apply(result)
        result.sort(key=lambda x: x.title)
        return self.viewIterator(result)
