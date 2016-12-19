#
#  Copyright (c) 2016 Helmut Merz helmutm@cy55.de
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
A view (to be used by listings, portlets, ...) for favorites.
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.configurator import ViewConfigurator, MacroViewProperty
from loops.browser.node import NodeView
from loops.common import adapted
from loops.organize.party import getPersonForUser
from loops.organize.personal.interfaces import IFavorites
from loops import util


personal_macros = ViewPageTemplateFile('personal_macros.pt')


class FavoriteView(NodeView):

    @Lazy
    def item(self):
        return self

    @Lazy
    def person(self):
        return getPersonForUser(self.context, self.request)

    @Lazy
    def favorites(self):
        records = self.loopsRoot.getRecordManager()
        if records is not None:
            storage = records.get('favorites')
            if storage is not None:
                return IFavorites(storage)
        return None

    def listFavorites(self):
        if self.favorites is None:
            return
        for uid in self.favorites.list(self.person):
            obj = util.getObjectForUid(uid)
            if obj is not None:
                adobj = adapted(obj)
                yield dict(url=self.getUrlForTarget(obj),
                           uid=uid,
                           title=adobj.favTitle,
                           description=adobj.description,
                           object=obj)

    def add(self):
        if self.favorites is None:
            return
        uid = self.request.get('id')
        if not uid:
            return
        obj = util.getObjectForUid(uid)
        self.favorites.add(obj, self.person)
        self.request.response.redirect(self.virtualTargetUrl)

    def remove(self):
        if self.favorites is None:
            return
        uid = self.request.get('id')
        if not uid:
            return
        obj = util.getObjectForUid(uid)
        self.favorites.remove(obj, self.person)
        self.request.response.redirect(self.virtualTargetUrl)
