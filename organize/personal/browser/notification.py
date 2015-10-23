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
Notifications listing.
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from loops.browser.concept import ConceptView
from loops.organize.personal.notification import Notifications
from loops.organize.party import getPersonForUser
from loops import util


personal_macros = ViewPageTemplateFile('personal_macros.pt')


class NotificationsListing(ConceptView):

    @Lazy
    def macro(self):
        return personal_macros.macros['notifications']

    @Lazy
    def person(self):
        return getPersonForUser(self.context, self.request)

    @Lazy
    def notifications(self):
        return Notifications(self.person)

    def getNotifications(self, unreadOnly=True):
        tracks = self.notifications.listTracks()
        return tracks
