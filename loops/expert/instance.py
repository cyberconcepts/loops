# loops.expert.instance

""" Filter query results.
"""

from zope.interface import implementer

from loops.expert.interfaces import IQueryInstance


@implementer(IQueryInstance)
class QueryInstance(object):

    def __init__(self, query, *filters, **kw):
        self.query = query
        self.filters = filters
        self.filterQueries = {}
        for k, v in kw.items():
            setattr(self, k, v)

    def apply(self, uidsOnly=False):
        result = self.query.apply()
        return result

