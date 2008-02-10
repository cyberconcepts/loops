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
Compound objects like articles, blog posts, storyboard items, ...

This is somehow related to cybertools.composer - so maybe we should
move part of the code defined here to that more generic package.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.interfaces import IConceptSchema
from loops.util import _


compoundPredicateName = 'ispartof'


class ICompound(IConceptSchema):
    """ A compound is a concept that is built up of other objects, its
        parts or components.

        These parts are typically resources, but may also be other
        concepts that may/should provide the ICompound interface as their
        type interface. The parts are assigned in an ordered way
        so that the parts are accessed in a reproducible order.

        The parts are bound to the compound via standard resource
        or concept relations using a special predicate, ``ispartof``.
    """

    def getParts():
        """ Return the objects (resources or other compounds) that
            this object consists of in the defined order.
        """

    def add(obj, position=None):
        """ Add a part to the compound.

            If the ``position`` argument is None, append it to the end
            of the current list of parts, otherwise insert it before
            the position given. The numbering of the positions is like for
            Python lists, so 0 means before the first one, -1 before the
            last one.
        """

    def remove(obj, position=None):
        """ Remove the object given from the context object's list of
            parts.

            If the object given is not present raise an error. If there
            is more than one part relation to the object given
            all of them will be removed, except if the position argument
            is given in which case only the object at the given position
            will be removed.
        """

    def reorder(parts):
        """ Change the order settings of the relations that connect the
            parts given (a sequence) to the compound so that they are
            ordered according to this sequence.

            If the parts`` argument contains a value that is not
            in the context objects`s list of parts raise an error. If the
            context object has parts that are not in the ``parts`` argument
            they will be moved to the end of the list.
        """
