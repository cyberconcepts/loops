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

from cybertools.browser.form import FormController
from cybertools.util.date import formatTimeStamp, getTimeStamp
from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.common import adapted, baseObject
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
        if self.person is None:
            return []
        tracks = self.notifications.listTracks(unreadOnly)
        return tracks

    def getNotificationsFormatted(self):
        unreadOnly = not self.request.form.get('show_all')
        result = []
        for track in self.getNotifications(unreadOnly):
            data = track.data
            s = util.getObjectForUid(data.get('sender'))
            sender = dict(label=s.title, 
                          url=self.nodeView.getUrlForTarget(baseObject(s)))
            obj = util.getObjectForUid(track.taskId)
            ov = self.nodeView.getViewForTarget(obj)
            url = '%s?form.action=notification_read&track=%s' % (
                    self.nodeView.getUrlForTarget(obj), 
                    util.getUidForObject(track))
            object = dict(label=ov.title, url=url)
            read_ts = self.formatTimeStamp(data.get('read_ts'))
            item = dict(timeStamp=self.formatTimeStamp(track.timeStamp),
                        sender=sender,
                        object=object,
                        text=data.get('text') or u'',
                        read_ts=read_ts)
            result.append(item)
        return result


class NotificationsView(NodeView, NotificationsListing):

    pass


class ReadNotification(FormController):

    def update(self):
        form = self.request.form
        trackId = form.get('track')
        track = util.getObjectForUid(trackId)
        data = track.data
        alreadyRead = data.get('read_ts')
        if not alreadyRead:
            data['read_ts'] = getTimeStamp()
        track.data = data
        return True
