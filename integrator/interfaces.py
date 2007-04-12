#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Intergrator interfaces.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.util import _


class IExternalCollection(Interface):
    """ A collection of resources, to be used for a concept adapter.
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
            required=False)
    address = schema.TextLine(
            title=_(u'Relative address'),
            description=_(u'Optional second (local) part of the '
                           'collection\'s address'),
            required=False)
    pattern = schema.TextLine(
            title=_(u'Selection pattern'),
            description=_(u'A regular expression for selecting external objects '
                           'that should belong to this collection'),
            required=False)

    def create():
        """ Select external objects that should belong to a collection
            using all the informations in the attributes,
            create a resource of type 'extfile' for each of them,
            and associate them with this collection.
            Fire appropriate events.
        """

    def update():
        """ Check for new, changed, or deleted external objects.
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
            return an iterable of local address parts of the selected external
            objects. The object specified by the 'clientCollection' argument
            is usually the caller of the method and should provide the
            IExternalCollection interface.
        """

    def createExtFileObjects(clientCollection, addresses, extFileType=None):
        """ Create a resource of type 'extFileType' (default is the
            type with the name 'extfile') for each of the addresses
            provided. Return the list of objects created.
        """


class IAutoClassifier(Interface):
    """ An adapter that more or less automagically assigns concepts to a
        resource using some sort of selection criteria for the concepts
        that should be considered.
    """


class IOntologyExporter(Interface):
    """ An adapter for creating an XML file with all appropriate informations
        from the context and its children, selecting children via a
        pattern or a set of selection criteria.

        This may then be used by an external tool for classifying
        a set of external objects.
    """


class IClassificationImporter(Interface):
    """ An Adapter for importing an XML file with classification
        information for a collection of external objects."
    """


