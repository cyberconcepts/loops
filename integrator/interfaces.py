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
Integrator interfaces.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.interfaces import IConceptSchema
from loops.util import _


class IExternalSourceInfo(Interface):
    """ Provide additional information about the external source
        of an object.
    """

    externalIdentifier = Attribute('A string that allows to uniquely '
                'identify a resource or concept that is provided by an '
                'external system, e.g. a client-base loops agent. ')


# external collections

class IExternalCollection(IConceptSchema):
    """ A concept representing a collection of resources that may be
        actively retrieved from an external system using the parameters
        given.
    """

    providerName = schema.TextLine(
            title=_(u'Provider name'),
            description=_(u'The name of a utility that provides the '
                           'external objects; default is a directory '
                           'collection provider'),
            required=False)
    baseAddress = schema.TextLine(
            title=_(u'Base address'),
            description=_(u'A base path or URL for accessing this collection '
                           'on the external system'),
            required=True)
    address = schema.TextLine(
            title=_(u'Relative address'),
            description=_(u'Optional second (local) part of the '
                          u'collection\'s address'),
            required=False)
    pattern = schema.TextLine(
            title=_(u'Selection pattern'),
            description=_(u'A regular expression for selecting external objects '
                           'that should belong to this collection'),
            required=False)
    lastUpdated = Attribute('Date and time of last update.')

    def update():
        """ Select external objects that should belong to a collection
            and check for new, changed, or deleted objects.
            Create an 'extfile' resource for new ones, fire appropriate
            events for new, changed, or deleted ones.
            Resources for deleted objects are not removed but should
            be empty; they also should receive some state change.
        """


class IExternalCollectionProvider(Interface):
    """ A utility that provides access to an external collection of objects.
    """

    def collect(clientCollection):
        """ Select objects that should belong to a collection,
            return an iterable of tuples of local address parts of the selected external
            objects and their last modification date/time.
            The object specified by the 'clientCollection' argument
            is usually the caller of the method and should provide the
            IExternalCollection interface.
        """

    def createExtFileObjects(clientCollection, addresses, extFileType=None):
        """ Create a resource of type 'extFileType' (default is the
            type with the name 'extfile') for each of the addresses
            provided. Return the list of objects created.
        """

