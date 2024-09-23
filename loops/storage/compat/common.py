# loops.storage.compat.common

"""Compatibility layer on scopes.storage: common functionality."""

from sqlalchemy import Table, Column, Index, Text

from scopes.storage import common
from scopes.storage.db import postgres


class Storage(common.Storage):

    uidTable = None

    def __init__(self, db, schema=None):
        super(Storage, self).__init__(db, schema)
        self.uidTable = self.getUidTable(self.schema)

    def storeUid(self, ouid, prefix, id):
        ouid = int(ouid)
        t = self.uidTable
        stmt = t.update().values(prefix=prefix, id=id).where(t.c.legacy == ouid)
        n = self.session.execute(stmt).rowcount
        if n == 0:
            stmt = t.insert().values(legacy=ouid, prefix=prefix, id=id)
            self.session.execute(stmt)
        self.mark_changed()

    def getUidTable(self, schema=None):
        #table = getExistingTable(self.storage, self.tableName)
        #if table is None:
        return createUidTable(self)


class StorageFactory(postgres.StorageFactory):

    storageClass = Storage


def createUidTable(storage):
    metadata = storage.metadata
    cols = [Column('legacy', storage.db.IdType, primary_key=True),
            Column('prefix', Text, nullable=False),
            Column('id', storage.db.IdType, nullable=False)]
    idxs = [Index('idx_uid_mapping_prefix_id', 'prefix', 'id', unique=True)]
    table = Table('uid_mapping', metadata, *(cols+idxs), extend_existing=True)
    metadata.create_all(storage.engine)
    return table
    
