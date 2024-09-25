# loops.expert.filter

""" Filter query results.
"""

from BTrees.IOBTree import IOBTree
from zope.interface import implementer

from cybertools.catalog.query import And
from loops.expert.interfaces import IFilter
from loops.expert.query import Children as ChildrenQuery
from loops import util


@implementer(IFilter)
class Filter(object):

    query = None

    def __init__(self, **kw):
        self.kwargs = kw

    def apply(self, objects, queryInstance=None):
        qu = self.query()
        #if qu is not None:
        #    return set(objects).intersection(qu.apply())
        result = IOBTree()
        for uid, obj in objects.items():
            if self.check(uid, obj, queryInstance):
                result[uid] = obj
        return result

    def check(self, uid, obj, queryInstance=None):
        return uid in self.query().apply()      #.keys()


@implementer(IFilter)
class Children(Filter):

    def __init__(self, parent, **kw):
        self.parent = parent
        super(Children, self).__init__(**kw)

    def query(self):
        return ChildrenQuery(self.parent, **self.kwargs)

