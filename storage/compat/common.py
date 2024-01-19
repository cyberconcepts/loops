# loops.storage.compat.common

"""Compatibility layer on cco.storage: common functionality."""

from cco.storage import common


class Storage(common.Storage):

    uidTable = None

    def __init__(self, engine, schema=None):
        super(Storage, self).__init__(engine, schema)
        #self.uidTable = self.getUidTable(self.schema)

    def getUidTable(self, schema=None):
        #table = getExistingTable(self.storage, self.tableName)
        #if table is None:
        return createUidTable(self.storage)


