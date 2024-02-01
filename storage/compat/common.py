# loops.storage.compat.common

"""Compatibility layer on cco.storage: common functionality."""

from sqlalchemy import Table, Column, BigInteger, Text
from zope.sqlalchemy import mark_changed

from cco.storage import common


class Storage(common.Storage):

    uidTable = None

    def __init__(self, schema=None):
        super(Storage, self).__init__(schema)
        self.uidTable = self.getUidTable(self.schema)

    def storeUid(self, ouid, nuid):
        ouid = int(ouid)
        t = self.uidTable
        stmt = t.update().values(standard=nuid).where(t.c.legacy == ouid)
        n = self.session.execute(stmt).rowcount
        if n == 0:
            stmt = t.insert().values(legacy=ouid, standard=nuid)
            self.session.execute(stmt)
        mark_changed(self.session)


    def getUidTable(self, schema=None):
        #table = getExistingTable(self.storage, self.tableName)
        #if table is None:
        return createUidTable(self)


def createUidTable(storage):
    metadata = storage.metadata
    cols = [Column('legacy', BigInteger, primary_key=True),
            Column('standard', Text, nullable=False, unique=True, index=True)]
    table = Table('uid_mapping', metadata, *cols, extend_existing=True)
    metadata.create_all(storage.engine)
    return table
    
