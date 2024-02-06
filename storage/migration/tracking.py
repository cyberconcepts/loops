# loops.storage.migration.tracking

"""Tools for migration of ZODB-/BTree-based tracks to SQL-based records."""

from datetime import datetime
import transaction

import config
import cco.storage.common
from cco.storage.common import getEngine, sessionFactory
from cco.storage import tracking
from loops.config.base import LoopsOptions
from loops.storage.compat.common import Storage
from loops import util


def migrate(loopsRoot, source, factory=tracking.Container,
            start=0, stop=None, step=10):
    if isinstance(source, basestring):
        rf = loopsRoot.getRecordManager().get(source)
        if rf is None:
            print('*** ERROR: folder %r not found!' % recFolderName)
            return
        items = rf.items()[start:stop]
    else:
        items = [(s.__name__, s) for s in source[start:stop]]
    options = LoopsOptions(loopsRoot)
    #print('*** database:', config.dbname, config.dbuser, config.dbpassword)
    schema = options('cco.storage.schema') or None
    if schema is not None:
        schema = schema[0]
    #print('*** schema:', schema)
    storage = Storage(schema=schema)
    container = storage.create(factory)
    for ix, (id, inTrack) in enumerate(items):
        ts = datetime.fromtimestamp(inTrack.timeStamp)
        #print('*** in:', id, inTrack)
        head = [inTrack.metadata[k] for k in container.itemFactory.headFields]
        #print('*** out:', head, ts)
        track = container.itemFactory(*head, trackId=int(id), 
                                    timeStamp=ts, data=inTrack.data)
        container.upsert(track)
        ouid = util.getUidForObject(inTrack)
        storage.storeUid(ouid, track.uid)
        if divmod(ix+1, step)[1] == 0:
            print('*** migrated %d' % (ix + 1 + start))
            transaction.commit()
    transaction.commit()

