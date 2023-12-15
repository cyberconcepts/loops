# loops.organize.tracking.storage.migration

"""Tools for migration ZODB-/BTree-based tracks to SQL-base records."""

from datetime import datetime

import config
from cco.storage.common import Storage, getEngine
from cco.storage.tracking import record
from loops.config.base import LoopsOptions


def migrate(loopsRoot, recFolderName, factory=record.Container):
    rf = loopsRoot.getRecordManager().get(recFolderName)
    if rf is None:
        print('*** ERROR: folder %r not found!' % recFolderName)
        return
    options = LoopsOptions(loopsRoot)
    print('*** database:', config.dbname, config.dbuser, config.dbpassword)
    schema = options('cco.storage.schema') or None
    if schema is not None:
        schema = schema[0]
    print('*** schema:', schema)
    storage = Storage(getEngine(config.dbengine, config.dbname, 
                                config.dbuser, config.dbpassword, 
                                host=config.dbhost, port=config.dbport), 
                      schema=schema)
    container = storage.create(factory)
    for id, inTrack in rf.items():
        ts = datetime.fromtimestamp(inTrack.timeStamp)
        print('*** in:', id, inTrack)
        head = [inTrack.metadata[k] for k in container.itemFactory.headFields]
        print('*** out:', head, ts)
        track = container.itemFactory(*head, trackId=int(id), 
                                    timeStamp=ts, data=inTrack.data)
        container.upsert(track)

