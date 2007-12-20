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

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.util import _


class ICompound(Interface):
    """ A compound is a concept that is built up of other objects, its
        components.

        These components are typically resources, but may also be other
        concepts that should provide the ICompound interface as their
        type interface. The components are assigned in an ordered way
        so that the components are accessed in a reproducible order.

        The components are bound to the compound via standard resource
        or concept relations using a special predicate, ``ispartof``.
    """

    components = Attribute('Objects (resources or other compounds) that '
                    'this object consists of')

    def add(obj, position=None):
        """ Add a component to the compound.

            If the ``position`` argument is None, append it to the end
            of the current list of components, otherwise insert it before
            the position given. The numbering of the positions is like for
            Python lists, so 0 means before the first one, -1 before the
            last one.
        """

    def reorder(components):
        """ Change the order settings of the relations that connect the
            components given (a sequence) to the compound so that they are
            ordered according to this sequence.
        """
