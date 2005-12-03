#
#  Copyright (c) 2004 Helmut Merz helmutm@cy55.de
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
loops interface definitions.

$Id$
"""

from zope.interface import Interface
from zope.i18nmessageid import MessageFactory
from zope import schema

_ = MessageFactory('loops')


class IConcept(Interface):
    """ The 'concept' is the central element of the loops framework.
        A concept is related to other concepts.
    """

    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Name or short title of the concept'),
        default=u'',
        required=True)

    def getSubConcepts(relationships=None):
        """ Return a tuple of concepts related to self as sub-concepts,
            possibly restricted to the relationships (typically a list of
            relation classes) given.
        """

    def getParentConcepts(relationships=None):
        """ Return a tuple of concepts related to self as parent concepts,
            possibly restricted to the relationships (typically a list of
            relation classes) given.
        """

    def assignConcept(concept, relationship):
        """ Assign an existing concept to self using the relationship given.
            The assigned concept will be a sub-concept of self.
        """

    def deassignConcept(concept, relationships=None):
        """ Remove the relations to the concept given from self, optionally
            restricting them to the relationships given.
        """

