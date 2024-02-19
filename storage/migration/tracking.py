# loops.storage.migration.tracking

"""Tools for migration of ZODB-/BTree-based tracks to SQL-based records."""

from datetime import datetime
import transaction

import config
import scopes.storage.common
from scopes.storage.common import getEngine, sessionFactory
from scopes.storage import tracking
from loops.config.base import LoopsOptions
from loops.storage.compat.common import Storage
from loops import util


def migrate(loopsRoot, source, factory=tracking.Container,
            start=0, stop=None, step=10, autoDelete=False):
    if isinstance(source, basestring):
        rf = loopsRoot.getRecordManager().get(source)
        if rf is None:
            print('*** ERROR: folder %r not found!' % recFolderName)
            return
        items = list(rf.items()[start:stop])
    else:
        items = [(s.__name__, s) for s in source[start:stop]]
    options = LoopsOptions(loopsRoot)
    #print('*** database:', config.dbname, config.dbuser, config.dbpassword)
    schema = options('scopes.storage.schema') or None
    if schema is not None:
        schema = schema[0]
    #print('*** schema:', schema)
    storage = Storage(schema=schema)
    container = storage.create(factory)
    ix = 0
    prefix = factory.itemFactory.prefix
    for ix, (id, inTrack) in enumerate(items):
        id = int(id)
        ts = datetime.fromtimestamp(inTrack.timeStamp)
        #print('*** in:', id, inTrack)
        head = [inTrack.metadata[k] for k in container.itemFactory.headFields]
        data = inTrack.data
        #print('*** out:', head, ts)
        for k, v in inTrack.__dict__.items():
            if k[0] == '_' and k[1] != '_':
                print('*** _field!', k, v, head)
                data[k] = v
        track = container.itemFactory(*head, trackId=id, 
                                    timeStamp=ts, data=data)
        container.upsert(track)
        ouid = util.getUidForObject(inTrack)
        storage.storeUid(ouid, prefix, id)
        if autoDelete:
            inTrack.__parent__.removeTrack(inTrack)
        if divmod(ix+1, step)[1] == 0:
            print('*** migrated %d' % (ix + 1 + start))
            transaction.commit()
    transaction.commit()
    print('*** migrated %d' % (ix + 1 + start))

