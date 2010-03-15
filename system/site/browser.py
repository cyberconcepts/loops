#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
Infos about loops sites.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.security import canAccess
from zope.traversing.api import getParent, getRoot, traverse
from zope.traversing.browser import absoluteURL

from cybertools.browser.action import actions
from loops.browser.action import DialogAction
from loops.browser.common import BaseView, adapted
from loops.browser.concept import ConceptView
from loops.system.site.interfaces import ILink
from loops import util
from loops.util import _


site_macros = ViewPageTemplateFile('view_macros.pt')


actions.register('createPortalLink', 'portlet', DialogAction,
        title=_(u'Create Link...'),
        description=_(u'Create a link to a loops site.'),
        viewName='create_concept.html',
        dialogName='createPortalLink',
        typeToken='.loops/concepts/portal_link',
        fixedType=True,
        innerForm='inner_concept_form.html',
)

actions.register('editPortalLink', 'portlet', DialogAction,
        title=_(u'Edit Link...'),
        description=_(u'Modify link.'),
        viewName='edit_concept.html',
        dialogName='editPortalLink',
)

class PortalPage(ConceptView):
    """ A query view linking to pages on other loops sites.
    """

    @Lazy
    def site_macros(self):
        return site_macros.macros

    @property
    def macro(self):
        return self.site_macros['portal_page']

    @Lazy
    def root(self):
        return getRoot(self.context)

    @Lazy
    def portalLinks(self):
        result = []
        for c in self.context.getChildren():
            link = adapted(c)
            if ILink.providedBy(link):
                site = traverse(self.root, link.site)
                path = link.path or 'home'
                target = traverse(site, 'views/' + path)
                if canAccess(target, 'title'):
                    siteInfo = SiteDetails(target, self.request)
                    siteInfo.title = link.title
                    if link.description:
                        siteInfo.description = link.description
                    if link.url:
                        siteInfo.url = link.url
                    result.append(siteInfo)
        return result


class SiteDetails(BaseView):

    pass


# old loops_sites.html view

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

