#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
Adapters for IConcept providing interfaces from the
cybertools.knowledge package.
"""

from zope import interface, component
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from cybertools.knowledge.interfaces import IKnowledgeElement, IKnowledgeProvider
from cybertools.knowledge.knowing import Knowing
from loops.common import ParentRelationSetProperty, ChildRelationSetProperty
from loops.interfaces import IConcept, IResource
from loops.i18n.common import I18NAdapterBase
from loops.knowledge.interfaces import IPerson, ITask, ITopic
from loops.organize.party import Person as BasePerson
from loops.organize.task import Task as BaseTask
from loops.common import AdapterBase
from loops.type import TypeInterfaceSourceList


# register type interfaces - (TODO: use a function for this)

TypeInterfaceSourceList.typeInterfaces += (IPerson, ITopic, IKnowledgeElement,
                                           ITask, IKnowledgeProvider)


class KnowledgeAdapterMixin(object):

    @Lazy
    def conceptManager(self):
        return self.context.getLoopsRoot().getConceptManager()

    @Lazy
    def standardPred(self):
        return self.conceptManager.getDefaultPredicate()

    @Lazy
    def dependsPred(self):
        return self.conceptManager['depends']

    @Lazy
    def knowsPred(self):
        return self.conceptManager['knows']

    @Lazy
    def requiresPred(self):
        return self.conceptManager['requires']

    @Lazy
    def providesPred(self):
        return self.conceptManager['provides']

    def __eq__(self, other):
        return self.context == other.context


class Person(BasePerson, Knowing, KnowledgeAdapterMixin):
    """ A typeInterface adapter for concepts of type 'person', including
        knowledge/learning management features.
    """

    _adapterAttributes = BasePerson._adapterAttributes + ('knowledge',)
    _noexportAttributes = ('knowledge',)

    knowledge = ParentRelationSetProperty('knows')

    implements(IPerson)

    def getKnowledge(self):
        return (IKnowledgeElement(c)
                for c in self.context.getParents((self.knowsPred,)))

    def knows(self, obj):
        self.context.assignParent(obj.context, self.knowsPred)

    def removeKnowledge(self, obj):
        self.context.deassignParent(obj.context, (self.knowsPred,))


class Topic(I18NAdapterBase, KnowledgeAdapterMixin):
    """ A typeInterface adapter for concepts of type 'topic' that
        may act as a knowledge element.
    """

    implements(ITopic)
    _adapterAttributes = I18NAdapterBase._adapterAttributes + ('parent',)

    def getParent(self):
        parents = self.context.getParents((self.standardPred,))
        return parents and IKnowledgeElement(parents[0]) or None
    def setParent(self, obj):
        old = self.getParent()
        if old is not None and old.context != self.context:
            self.context.deassignParent(old.context, (self.standardPred,))
        self.context.assignParent(obj.context, self.standardPred)
    parent = property(getParent, setParent)

    def getDependencies(self):
        return (IKnowledgeElement(c)
                for c in self.context.getParents((self.dependsPred,)))

    def dependsOn(self, obj):
        self.context.assignParent(obj.context, self.dependsPred)

    def removeDependency(self, obj):
        self.context.deassignParent(obj.context, (self.dependsPred,))

    def getDependents(self):
        return (IKnowledgeElement(c)
                for c in self.context.getChildren((self.dependsPred,)))

    def getKnowers(self):
        return (IPerson(c)
                for c in self.context.getChildren((self.knowsPred,)))

    def getProviders(self):
        return (IKnowledgeProvider(c)
                for c in self.context.getChildren((self.providesPred,))
                       + self.context.getResources((self.providesPred,)))


class Task(BaseTask, KnowledgeAdapterMixin):
    """ A typeInterface adapter for concepts of type 'task' that
        may act as a knowledge requirement profile.
    """

    implements(ITask)

    _adapterAttributes = BasePerson._adapterAttributes + ('requirements',)
    _noexportAttributes = ('requirements',)

    requirements = ParentRelationSetProperty('requires')

    def getRequirements(self):
        return (IKnowledgeElement(c)
                for c in self.context.getParents((self.requiresPred,)))

    def requires(self, obj):
        self.context.assignParent(obj.context, self.requiresPred)

    def removeRequirement(self, obj):
        self.context.deassignParent(obj.context, (self.requiresPred,))

    def getCandidates(self):
        result = []
        candidates = []
        reqs = list(self.requirements)
        for req in reqs:
            for p in req.getKnowers():
                if p not in candidates:
                    candidates.append(p)
                    item = dict(person=p, required=[], other=[], fit=0.0)
                    for k in p.knowledge:
                        if k in reqs:
                            item['required'].append(k)
                            item['fit'] += 1.0
                        else:
                            item['other'].append(k)
                    result.append(item)
        for item in result:
            item['fit'] = round(item['fit'] / len(reqs), 2)
        return sorted(result, key=lambda x: (-x['fit'], x['person'].title))


class ConceptKnowledgeProvider(AdapterBase, KnowledgeAdapterMixin):

    implements(IKnowledgeProvider)

    def getProvidedKnowledge(self):
        return (IKnowledgeElement(c)
                for c in self.context.getParents((self.providesPred,)))

    def provides(self, obj):
        self.context.assignParent(obj.context, self.providesPred)

    def removeProvidedKnowledge(self, obj):
        self.context.deassignParent(obj.context, (self.providesPred,))


class ResourceKnowledgeProvider(AdapterBase, KnowledgeAdapterMixin):

    implements(IKnowledgeProvider)
    adapts(IResource)

    def getProvidedKnowledge(self):
        return (IKnowledgeElement(c)
                for c in self.context.getConcepts((self.providesPred,)))

    def provides(self, obj):
        self.context.assignConcept(obj.context, self.providesPred)

    def removeProvidedKnowledge(self, obj):
        self.context.deassignConcept(obj.context, (self.providesPred,))

