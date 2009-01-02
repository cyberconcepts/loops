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
View class(es) for work items.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.security import canAccess
from zope.traversing.api import getParent, getRoot, traverse
from zope.traversing.browser import absoluteURL

from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops import util
from loops.util import _


site_macros = ViewPageTemplateFile('view_macros.pt')


class SitesListing(ConceptView):

    @Lazy
    def site_macros(self):
        return site_macros.macros

    @property
    def macro(self):
        return self.site_macros['sites_listing']

    @Lazy
    def root(self):
        return getRoot(self.context)

    @Lazy
    def sites(self):
        result = []
        paths = self.options('system.sites') or []
        for p in paths:
            s = traverse(self.root, p)
            if canAccess(s, 'title'):
                result.append(SiteDetails(s, self.request))
        return result


class SiteDetails(BaseView):

    pass
