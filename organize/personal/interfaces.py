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
Interface definitions for favorites/clipboard/navigation history.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import schema

from cybertools.tracking.interfaces import ITrack


class IFavorites(Interface):
    """ A collection of favorites.
    """

    def add(obj, person):
        """ Add an object to the person's favorites collection.
        """

    def remove(obj, person):
        """ Remove an object from the person's favorites collection.
        """

    def list(person, sortKey=None):
        """ Return a list of favorite objects for the person given.
        """


class IFavorite(ITrack):
    """ A favorite references a content object via the
        task id attribute; the user name references
        the user/person for which the favorite is to be stored.
        The tracking storage's run management is not used.
    """


class IFilters(Interface):
    """ A collection of filters.
    """

    def add(title, filter, person):
        """ Add a filter specification (a mapping) to the person's
            filters collection using the title given.
        """

    def activate(id):
        """ Activate the filter specified by its ID.
        """

    def deactivate(id):
        """ Deactivate the filter specified by its ID.
        """

    def remove(id):
        """ Remove the filter specified by its ID from the person's
            favorites collection.
        """

    def list(person, activeOnly=True, sortKey=None):
        """ Return a list of filters for the person given.
        """


class IFilter(ITrack):
    """ A filter is a stored query that will be used for restricting the result
        set of child and resource listings as well as explicit searches.
        It usually references a parent concept via the task id attribute.
        The user/person for which the filter is to be stored.
        The tracking storage's run management is not used.
    """
