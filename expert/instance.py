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

from zope.interface import implements

from loops.expert.interfaces import IQueryInstance


class QueryInstance(object):

    implements(IQueryInstance)

    def __init__(self, query, *filters, **kw):
        self.query = query
        self.filters = filters
        self.filterQueries = {}
        for k, v in kw.items():
            setattr(self, k, v)

    def apply(self, uidsOnly=False):
        result = self.query.apply()
        return result

