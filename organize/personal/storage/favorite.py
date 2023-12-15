# loops.organize.personal.storage.favorite

"""SQL-based storage for personal favorites and settings."""

from cco.storage.common import registerContainerClass
from cco.storage.tracking import record


class Favorite(record.Track):

    prefix = 'fav'


@registerContainerClass
class Favorites(record.Container):

    itemFactory = Favorite
    tableName = 'favorites'
    insertOnChange = False

