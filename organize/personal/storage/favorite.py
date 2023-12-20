# loops.organize.personal.storage.favorite

"""SQL-based storage for personal favorites and settings."""

from cco.storage.common import registerContainerClass
from loops.organize.personal.favorite import BaseFavorite
from loops.organize.tracking.storage import compat


class Favorite(BaseFavorite, compat.Track):

    prefix = 'fav'


@registerContainerClass
class Favorites(compat.Container):

    itemFactory = Favorite
    tableName = 'favorites'
    insertOnChange = False

