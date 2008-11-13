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
View class(es) for change tracks.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName

from cybertools.tracking.browser import TrackView
from loops import util


class ChangeView(TrackView):

    @Lazy
    def task(self):
        uid = self.metadata['taskId']
        return util.getObjectForUid(uid)

    @Lazy
    def taskTitle(self):
        task = self.task
        if task is None:
            return self.metadata['taskId']
        return getattr(task, 'title', getName(task))

    @Lazy
    def taskUrl(self):
        task = self.task
        if task is not None:
            return '%s/@@SelectedManagementView.html' % absoluteURL(task, self.request)

    @Lazy
    def user(self):
        uid = self.metadata['userName']
        if uid.isdigit():
            obj = util.getObjectForUid(uid)
            if obj is not None:
                return obj
        return uid

    @Lazy
    def userTitle(self):
        if isinstance(self.user, basestring):
            return self.user
        return getattr(self.user, 'title', getName(self.user))

    @Lazy
    def userUrl(self):
        user = self.user
        if user is not None and not isinstance(user, basestring):
            return '%s/@@introspector.html' % absoluteURL(user, self.request)


class AccessView(ChangeView):

    pass
