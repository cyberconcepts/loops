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
Filtering query result sets.

$Id$
"""

from zope.interface import Interface, Attribute


class IQuery(Interface):
    """ A query.
    """

    def apply():
        """ Return the result set for this query.
        """


class IQueryInstance(Interface):
    """ A top-level query instance that allows caching of intermediate
        results when the underlying queries and filters are applied.
    """

    query = Attribute('The top-level query (query term).')
    filters = Attribute('A collection of filters that will be applied '
                    'to the result of the query.')

    def apply(uidsOnly=False):
        """ Execute the query and apply the filters; return a mapping
            of UIDs to objects or a set of UIDs only if the ``uidsOnly``
            argument is set to True.
        """


class IFilter(Interface):
    """ A filter is a query that will be ``and``-connected to a query.
    """

    def query():
        """ Return the query that corresponds to this filter; that will then
            typically be ``and``-joined to another query.
            May return None; in this case the ``apply()`` method must be used.
        """

    def apply(objects, queryInstance=None):
        """ Apply the filter to the set of objects specified as a mapping
            of UIDs to objects.

            If a query instance is given it may be used for caching
            intermediate results.
        """

    def check(uid, obj, queryInstance=None):
        """ Return True if the object given should be included in the
            filter's result set, False otherwise.

            If a query instance is given it may be used for caching.
        """
