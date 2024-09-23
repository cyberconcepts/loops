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


class Base(ConceptView):

    @Lazy
    def site_macros(self):
        return site_macros.macros

    @Lazy
    def root(self):
        return getRoot(self.context)


class PortalPage(Base):
    """ A query view linking to pages on other loops sites.
    """

    @property
    def macro(self):
        return self.site_macros['portal_page']

    @Lazy
    def portalLinks(self):
        result = []
        for c in self.context.getChildren():
            info = PortalLink(c, self.request).targetInfo
            if info is not None:
                result.append(info)
        return result


class LinkInfo(BaseView):

    pass


class PortalLink(Base):

    @property
    def macro(self):
        return self.site_macros['portal_link']

    @Lazy
    def targetInfo(self):
        link = self.adapted
        if not ILink.providedBy(link):
            return None
        site = traverse(self.root, link.site, None)
        if site is None:
            return None
        path = link.path or 'home'
        target = traverse(site, 'views/' + path, None)
        if target is None:
            return None
        if not canAccess(target, 'title'):
            return None
        info = LinkInfo(target, self.request)
        info.title = link.title
        if link.description:
            info.description = link.description
        if link.url:
            info.url = link.url
        return info


# old loops_sites.html view

class SitesListing(Base):

    @property
    def macro(self):
        return self.site_macros['sites_listing']

    @Lazy
    def sites(self):
        result = []
        paths = self.options('system.sites') or []
        for p in paths:
            s = traverse(self.root, p)
            if canAccess(s, 'title'):
                result.append(LinkInfo(s, self.request))
        return result

