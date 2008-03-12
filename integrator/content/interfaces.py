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
External content integration interfaces.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.interfaces import IConceptSchema
from loops.util import _


class IExternalAccess(IConceptSchema):
    """ A concept adapter providing access to objects in an external system.
    """

    providerName = schema.TextLine(
            title=_(u'Provider name'),
            description=_(u'The name of a utility that provides access to the '
                           'external objects, typically a factory of proxy '
                           'objects.'),
            required=False)
    baseAddress = schema.TextLine(
            title=_(u'Base address'),
            description=_(u'A base path or URL for accessing the external '
                           'object.'),
            required=True)
    address = schema.TextLine(
            title=_(u'Relative address'),
            description=_(u'Optional second (local) part of the '
                           'external objects\'s address, e.g. a directory name.'),
            required=False)
    pattern = schema.TextLine(
            title=_(u'Selection pattern'),
            description=_(u'A regular expression for selecting external objects '
                           'that should be made accessible.'),
            required=False)

    def __call__():
        """ Return an object representing the top-level external object.
            This is typically a container proxy.
        """
