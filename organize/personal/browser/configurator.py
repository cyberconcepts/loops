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
A view configurator provides configuration data for a view controller.

$Id$
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.cachedescriptors.property import Lazy
from zope.traversing.browser.absoluteurl import absoluteURL

from cybertools.browser.configurator import ViewConfigurator, MacroViewProperty
from loops.organize.party import getPersonForUser
from loops.util import _


personal_macros = ViewPageTemplateFile('personal_macros.pt')


class PortletConfigurator(ViewConfigurator):
    """ Specify portlets.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def hasFavorites(self):
        records = self.context.getLoopsRoot().getRecordManager()
        if records is not None:
            return 'favorites' in records
        return False

    @property
    def viewProperties(self):
        if (not self.hasFavorites()
            or getPersonForUser(self.context, self.request) is None):
        #if IUnauthenticatedPrincipal.providedBy(self.request.principal):
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

