# loops.storage.migration.tracking

"""Tools for migration of ZODB-/BTree-based tracks to SQL-based records."""

from datetime import datetime
import transaction

from scopes.storage import tracking
from loops.config.base import LoopsOptions
from loops import util


def migrate(loopsRoot, recFolderName, sourceIds=None, factory=tracking.Container,
            start=0, stop=None, step=10, autoDelete=False):
    rf = loopsRoot.getRecordManager().get(recFolderName)
    if rf is None:
        print('*** ERROR: folder %r not found!' % recFolderName)
        return
    if sourceIds is None:
        trackIds = list(rf.keys()[start:stop])
    else:
        trackIds = sourceIds[start:stop]
    options = LoopsOptions(loopsRoot)
    schema = options('scopes.storage.schema') or None
    if schema is not None:
        schema = schema[0]
    #print('*** schema:', schema)
    storage = util.storageFactory(schema=schema)
    container = storage.create(factory)
    ix = 0
    prefix = factory.itemFactory.prefix
    for ix, id in enumerate(trackIds):
        inTrack = rf[id]
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

