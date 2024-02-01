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


def migrate(loopsRoot, recFolderName, factory=tracking.Container):
    rf = loopsRoot.getRecordManager().get(recFolderName)
    if rf is None:
        print('*** ERROR: folder %r not found!' % recFolderName)
        return
    options = LoopsOptions(loopsRoot)
    #print('*** database:', config.dbname, config.dbuser, config.dbpassword)
    schema = options('cco.storage.schema') or None
    if schema is not None:
        schema = schema[0]
    #print('*** schema:', schema)
    storage = Storage(schema=schema)
    container = storage.create(factory)
    for id, inTrack in rf.items():
        ts = datetime.fromtimestamp(inTrack.timeStamp)
        #print('*** in:', id, inTrack)
        head = [inTrack.metadata[k] for k in container.itemFactory.headFields]
        #print('*** out:', head, ts)
        track = container.itemFactory(*head, trackId=int(id), 
                                    timeStamp=ts, data=inTrack.data)
        container.upsert(track)
        ouid = util.getUidForObject(inTrack)
        storage.storeUid(ouid, track.uid)
    transaction.commit()

