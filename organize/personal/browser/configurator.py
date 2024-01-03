#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
A view configurator provides configuration data for a view controller.
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.cachedescriptors.property import Lazy
from zope.traversing.browser.absoluteurl import absoluteURL

from cybertools.browser.configurator import ViewConfigurator, MacroViewProperty
from cybertools.meta.interfaces import IOptions
from loops.browser.node import NodeView
from loops.organize.party import getPersonForUser
from loops.organize.personal.notification import Notifications
from loops.util import _


personal_macros = ViewPageTemplateFile('personal_macros.pt')


class PortletConfigurator(ViewConfigurator):
    """ Specify portlets.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.view = NodeView(self.context, self.request)

    @property
    def viewProperties(self):
        return self.favorites + self.filters + self.notifications

    @Lazy
    def records(self):
        return self.context.getLoopsRoot().getRecordManager()

    @Lazy
    def person(self):
        return getPersonForUser(self.context, self.request)

    def hasFavorites(self):
        if 'favorites' in (self.view.globalOptions.cco.storage.records or []):
            return True
        if self.records is not None:
            return 'favorites' in self.records
        return False

    def hasFilters(self):
        if (IOptions(self.context.getLoopsRoot()).organize.useFilters and
                self.records is not None):
            return 'filters' in self.records
        return False

    @property
    def favorites(self):
        if (not self.hasFavorites() or self.person is None):
            return []
        favorites = MacroViewProperty(self.context, self.request)
        favorites.setParams(dict(
                    slot='portlet_right',
                    identifier='loops.organize.favorites',
                    title=_(u'Favorites'),
                    subMacro=personal_macros.macros['favorites_portlet'],
                    priority=200,
                    #url=absoluteURL(self.context, self.request) + '/@@favorites.html',
        ))
        return [favorites]

    @property
    def filters(self):
        if (not self.hasFilters() or self.person is None):
            return []
        filters = MacroViewProperty(self.context, self.request)
        filters.setParams(dict(
                    slot='portlet_right',
                    identifier='loops.organize.filters',
                    title=_(u'Filters'),
                    subMacro=personal_macros.macros['filters_portlet'],
                    priority=195,
                    #url=absoluteURL(self.context, self.request) + '/@@filters.html',
        ))
        return [filters]

    @property
    def notifications(self):
        if self.person is None:
            return []
        notif = self.view.globalOptions.organize.showNotifications
        if not notif:
            return []
        if not list(Notifications(self.person).listTracks(unreadOnly=False)):
            return []
        if isinstance(notif, list):
            notifPage = notif[0]
        else:
            notifPage = 'notifications'
        portlet = MacroViewProperty(self.context, self.request)
        portlet.setParams(dict(
                    slot='portlet_left',
                    identifier='loops.organize.notifications',
                    title=_(u'Notifications'),
                    subMacro=personal_macros.macros['notifications_portlet'],
                    priority=10,
                    url='%s/%s' % (self.view.menu.url, notifPage),
        ))
        return [portlet]
