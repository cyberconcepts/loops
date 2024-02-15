# loops.organize.personal.storage.favorite

"""SQL-based storage for personal favorites and settings."""

from scopes.storage.common import registerContainerClass
from loops.organize.personal.favorite import BaseFavorite
from loops.storage.compat import tracking


class Favorite(BaseFavorite, tracking.Track):

    prefix = 'fav'


@registerContainerClass
class Favorites(tracking.Container):

    itemFactory = Favorite
    tableName = 'favorites'
    insertOnChange = False

