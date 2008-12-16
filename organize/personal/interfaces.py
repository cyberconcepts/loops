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
