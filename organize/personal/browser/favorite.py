# loops.organize.personal.browser

"""A view (to be used by listings, portlets, ...) for favorites.
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

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

    @Lazy
    def item(self):
        return self

    @Lazy
    def person(self):
        return getPersonForUser(self.context, self.request)

    @Lazy
    def favorites(self):
        return FavAdapter(util.records(self.context, 'favorites', Favorites))

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
