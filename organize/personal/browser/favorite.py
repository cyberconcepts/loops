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

import config
from cco.storage.common import Storage, getEngine
from cybertools.browser.configurator import ViewConfigurator, MacroViewProperty
from loops.browser.node import NodeView
from loops.common import adapted
from loops.organize.party import getPersonForUser
from loops.organize.personal.favorite import Favorites as FavAdapter
from loops.organize.personal.interfaces import IFavorites
from loops.organize.personal.storage.favorite import Favorites
from loops import util


personal_macros = ViewPageTemplateFile('personal_macros.pt')


class FavoriteView(NodeView):

    containerName = 'favorites'
    containerFactory = Favorites

    @Lazy
    def useRecordsStorage(self):
        return self.containerName in (self.globalOptions('cco.storage.records') or [])

    @Lazy
    def recordsContainer(self):
        schema = self.globalOptions('cco.storage.schema') or None
        if schema is not None:
            schema = schema[0]
        storage = Storage(getEngine(config.dbengine, config.dbname, 
                                config.dbuser, config.dbpassword, 
                                host=config.dbhost, port=config.dbport), 
                      schema=schema)
        return storage.create(self.containerFactory)

    @Lazy
    def item(self):
        return self

    @Lazy
    def person(self):
        return getPersonForUser(self.context, self.request)

    @Lazy
    def favorites(self):
        if self.useRecordsStorage:
            return FavAdapter(self.recordsContainer)
        records = self.loopsRoot.getRecordManager()
        if records is not None:
            storage = records.get('favorites')
            if storage is not None:
                return IFavorites(storage)
        return None

    def listFavorites(self):
        if self.favorites is None:
            return
        self.registerDojoDnd()
        form = self.request.form
        if 'favorites_change_order' in form:
            uids = form.get('favorite_uids')
            if uids:
                self.favorites.reorder(uids)
        for trackUid, uid in self.favorites.listWithTracks(self.person):
            obj = util.getObjectForUid(uid)
            if obj is not None:
                adobj = adapted(obj)
                yield dict(url=self.getUrlForTarget(obj),
                           uid=uid,
                           title=adobj.favTitle,
                           description=adobj.description,
                           object=obj,
                           trackUid=trackUid)

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
