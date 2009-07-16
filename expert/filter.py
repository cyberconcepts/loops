#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Filter query results.

$Id$
"""

from BTrees.IOBTree import IOBTree
from zope.interface import implements

from cybertools.catalog.query import And
from loops.expert.interfaces import IFilter
from loops.expert.query import Children as ChildrenQuery
from loops import util


class Filter(object):

    implements(IFilter)

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


class Children(Filter):

    implements(IFilter)

    def __init__(self, parent, **kw):
        self.parent = parent
        super(Children, self).__init__(**kw)

    def query(self):
        return ChildrenQuery(self.parent, **self.kwargs)

