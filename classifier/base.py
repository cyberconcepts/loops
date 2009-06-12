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
Adapters and others classes for analyzing resources.

$Id$
"""

from itertools import tee
from logging import getLogger
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.event import notify
from zope.interface import implements
from zope.traversing.api import getName, getParent
from cybertools.typology.interfaces import IType

from loops.classifier.interfaces import IClassifier, IExtractor, IAnalyzer
from loops.classifier.interfaces import IInformationSet, IStatement
from loops.common import AdapterBase, adapted
from loops.interfaces import IResource, IConcept
from loops.query import ConceptQuery
from loops.resource import Resource
from loops.setup import addAndConfigureObject
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IClassifier,)


class Classifier(AdapterBase):
    """ A concept adapter for analyzing resources.
    """

    implements(IClassifier)
    adapts(IConcept)

    _contextAttributes = list(IClassifier) + list(IConcept)

    logLevel = 5  # 99 don't log; 5 minimal logging; 0 full logging

    @Lazy
    def conceptManager(self):
        return self.context.getConceptManager()

    @Lazy
    def defaultPredicate(self):
        return self.conceptManager.getDefaultPredicate()

    @Lazy
    def predicateType(self):
        return self.conceptManager.getPredicateType()

    @Lazy
    def typeConcept(self):
        return self.conceptManager.getTypeConcept()

    def getOptions(self):
        return getattr(self.context, '_options', [])
    def setOptions(self, value):
        self.context._options = value
    options = property(getOptions, setOptions)

    def process(self, resource):
        self.log('Processing %s' % resource.title, 3)
        infoSet = InformationSet()
        for name in self.extractors.split():
            extractor = component.getAdapter(adapted(resource), IExtractor, name=name)
            infoSet.update(extractor.extractInformationSet())
        analyzer = component.getAdapter(self, IAnalyzer, name=self.analyzer)
        statements = analyzer.extractStatements(infoSet)
        for statement in statements:
            object = statement.object
            qualifiers = IType(object).qualifiers
            if 'system' in qualifiers:
                continue
            if statement.subject is None:
                statement.subject = resource
            if statement.predicate is None:
                statement.predicate = self.defaultPredicate
            self.assignConcept(statement.subject, object, statement.predicate)

    def assignConcept(self, resource, concept, predicate):
        resources = concept.getResources([predicate])
        if resource not in resources:
            concept.assignResource(resource, predicate)
            message = u'Assigning: %s %s %s'
        else:
            message = u'Already assigned: %s %s %s'
        self.log(message % (resource.title, predicate.title, concept.title), 4)

    def log(self, message, level=5):
        if level >= self.logLevel:
            #print 'Classifier %s:' % getName(self.context), message
            getLogger('Classifier').info(
                u'%s: %s' % (getName(self.context), message))


class Extractor(object):

    implements(IExtractor)
    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def extractInformationSet(self):
        return InformationSet()


class Analyzer(object):

    implements(IAnalyzer)
    adapts(IClassifier)

    def __init__(self, context):
        self.context = context

    def extractStatements(self, informationSet):
        return []

    @Lazy
    def query(self):
        return ConceptQuery(self.context)

    def findConcepts(self, word):
        r1, r2 = tee(self.query.query(word, 'loops:concept:*'))
        names = ', '.join(c.title for c in r2)
        self.context.log('Searching for concept using "%s", result: %s'
                       % (word, names), 2)
        return r1


class InformationSet(dict):

    implements(IInformationSet)


class Statement(object):

    implements(IStatement)

    def __init__(self, object=None, predicate=None, subject=None, relevance=100):
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.relevance = relevance

