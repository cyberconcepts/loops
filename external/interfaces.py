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
Interfaces for export and import of loops objects.

Maybe part of this stuff should be moved to cybertools.external.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema


class IElement(Interface):
    """ A dicionary-like information element that is able to represent a
        loops object, a relation between loops objects or a special attribute.
        The attributes of the object are represented by items of
        the dictionary; the attribute values may be strings, unicode strings,
        or IElement objects.
    """

    def __call__(loader):
        """ Create the object that is specified by the element in the
            context of the loader and return it.
        """


class IReader(Interface):
    """ Provides objects in an intermediate format from an external source.
        Will typically be implemented by an utility or an adapter.
    """

    def read():
        """ Retrieve content from the external source returning a sequence
            of IElement objects.
        """


class ILoader(Interface):
    """ Inserts data provided by an IReader object into the
        loops database/the context object. Will typically be used as an adapter.
    """

    def load(elements):
        """ Create the objects and relations specified by the ``elements``
            argument given.
        """


class IWriter(Interface):
    """ Transforms object information to an external storage.
    """

    def write(elements):
        """ Write the sequence of elements given in an external format.
        """


class IExtractor(Interface):
    """ Extracts information from loops objects and provides them as
        IElement objects. Will typically be used as an adapter.
    """

    def extract():
        """ Creates and returns a sequence of IElement objects by scanning
            the content of the context object.
        """

