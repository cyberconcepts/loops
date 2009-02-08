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
from loops import util
from loops.util import _


search_macros = ViewPageTemplateFile('search.pt')


class SearchResults(NodeView):
    """ Provides results listing """

    @Lazy
    def macro(self):
        return search_macros.macros['search_results']

    @Lazy
    def item(self):
        return self

    @Lazy
    def results(self):
        form = self.request.form
        text = form.get('search.text')
        type = self.globalOptions('expert.quicksearch')[0]
        result = FullQuery(self).query(text=text, type=type,
                           useTitle=True, useFull=True,)
        return self.viewIterator(result)
