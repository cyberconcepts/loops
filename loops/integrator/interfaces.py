#
#  Copyright (c) 2014 Helmut Merz helmutm@cy55.de
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
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.interfaces import IConceptSchema, ILoopsAdapter, IExternalFile
from loops.util import _


class IExternalSourceInfo(Interface):
    """ Provide additional information about the external source
        of an object.
    """

    externalIdentifier = Attribute('A string that allows to uniquely '
                'identify a resource or concept that is provided by an '
                'external system, e.g. a client-base loops agent. ')


# external collections

class IExternalCollection(IConceptSchema, ILoopsAdapter):
    """ A concept representing a collection of resources that may be
        actively retrieved from an external system using the parameters
        given.
    """

    providerName = schema.TextLine(
            title=_(u'Provider name'),
            description=_(u'The name of a utility that provides the '
                          u'external objects; default is a directory '
                          u'collection provider.'),
            required=False)
    baseAddress = schema.TextLine(
            title=_(u'Base address'),
            description=_(u'A base path or URL for accessing this collection '
                          u'on the external system.'),
            required=True)
    address = schema.TextLine(
            title=_(u'Relative address'),
            description=_(u'Optional second (local) part of the '
                          u'collection\'s address.'),
            required=False)
    pattern = schema.TextLine(
            title=_(u'Selection pattern'),
            description=_(u'A regular expression for selecting external objects '
                          u'that should belong to this collection.'),
            required=False)
    excludeDirectories = schema.Bool(
            title=_(u'Exclude directories'),
            description=_(u'Check this if only objects directly at the specified '
                          u'address should be included in the collection.'),
            default=False,
            required=False)
    exclude = schema.List(
            title=_(u'Exclude'),
            description=_(u'Names of objects (directories and files) that should not '
                          u'be included.'),
            value_type=schema.TextLine(),
            required=False)
    metaInfo = schema.Text(
            title=_(u'Meta Information'),
            description=_(u'A text giving some background information '
                          u'about a media asset, like source, rights, etc.'
                          u'This text will be applied to all resources '
                          u'belonging to this collection.'),
            default=u'',
            required=False)
    overwriteMetaInfo = schema.Bool(
            title=_(u'Overwrite Meta Information'),
            description=_(u'Check this if meta information already present '
                          u'should be overwritten by the new text given above.'),
            default=False,
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

    def createExtFileObjects(clientCollection, addresses, extFileTypes=None):
        """ Create a resource for each of the addresses provided.
            Return the list of objects created.

            The ``extFileTypes`` argument is a mapping of MIME types to
            names of concept types. The MIME types may contain wildcards,
            e.g. 'image/*', '*/*'.
        """

class IOfficeFile(IExternalFile):
    """ An external file that references a MS Office (2007/2010) file.
        It provides access to the document content and properties.
    """

    documentPropertiesAccessible = Attribute(
            'Are document properties accessible?')
