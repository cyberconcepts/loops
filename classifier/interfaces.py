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
Classifier interfaces.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.interfaces import IConceptSchema
from loops.util import _


class IClassifier(IConceptSchema):
    """ An object that is able to analyze a resource and identify the
        concepts to assign.
    """

    extractors = schema.TextLine(
        title=_(u'Extractors'),
        description=_(u'Space-separated list of names of extractor adapters.'),
        default=u'',
        required=False)

    analyzer = schema.TextLine(
        title=_(u'Analyzer'),
        description=_(u'Name of an adapter (or a utility?) that is able to '
                'analyze the resources assigned to this classifier.'),
        default=u'',
        required=False)

    options = schema.List(
        title=_(u'Options'),
        description=_(u'Additional settings...'),
        value_type=schema.TextLine(),
        default=[],
        required=False)

    def process(resource):
        """ Do all that is needed to classify the resource given.
        """

    def assignConcept(statement):
        """ Assign a concept representing the object of the statement
            given to the statement's subject, using the statement's
            predicate.
        """


class IExtractor(Interface):
    """ Adapter for extracting an information set from a resource.
    """

    def extractInformationSet():
        """ Return an information set based on the resource given.
        """


class IAnalyzer(Interface):
    """ Adapter (or utility?) that is able to analyze an information set and
        provide a collection of statements about it.
    """

    def extractStatements(informationSet):
        """ Return a collection of statements derived from the
            information set given.
        """


class IInformationSet(Interface):
    """ A mapping or collection of key/value pairs; the keys are usually the
        names of information elements, the values may be simple strings,
        structured resources (e.g. XML documents), files providing such strings
        or documents, or another kind of objects. The analyzer that is
        fed with this information set must know what to do with it.
    """


class IStatement(Interface):
    """ Represents a subject-predicate-object triple. These attributes
        may be strings denoting the real
    """

    subject = Attribute('Subject of the Statement')
    predicate = Attribute('Predicate of the Statement')
    object = Attribute('Object of the Statement')
    relevance = Attribute('A number denoting the relevance or correctness '
                    'of the statement')

