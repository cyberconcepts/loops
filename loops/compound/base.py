# loops.compound.base

""" Compound objects like articles, blog posts, storyboard items, ...
"""

from zope.cachedescriptors.property import Lazy
from zope.interface import implementer
from zope.traversing.api import getName

from loops.common import AdapterBase
from loops.compound.interfaces import ICompound, compoundPredicateNames


@implementer(ICompound)
class Compound(AdapterBase):

    compoundPredicateNames = compoundPredicateNames

    @Lazy
    def compoundPredicates(self):
        return [self.context.getConceptManager()[n] 
                    for n in self.compoundPredicateNames]

    def getParts(self):
        if self.context.__parent__ is None:
            return []
        return self.context.getResources(self.compoundPredicates)

    def add(self, obj, position=None):
        if position is None:
            order = self.getMaxOrder() + 1
        else:
            order = self.getOrderForPosition(position)
        self.context.assignResource(obj, self.partOf, 
                                    order=order)

    def remove(self, obj, position=None):
        if position is None:
            self.context.deassignResource(obj, self.compoundPredicates)
        else:
            rel = self.getPartRelations()[position]
            self.context.deassignResource(obj, self.compoundPredicates, 
                                          order=rel.order)

    def reorder(self, parts):
        existing = list(self.getPartRelations())
        order = 1
        for p in parts:
            for idx, x in enumerate(existing):
                if x.second == p:
                    x.order = order
                    order += 1
                    del existing[idx]
                    break
            else:
                raise ValueError("Part '%s' not in list of existing parts."
                                 % getName(p))
        for x in existing:  # position the rest at the end
            x.order = order
            order += 1

    # helper methods and properties

    def getPartRelations(self):
        return self.context.getResourceRelations(self.compoundPredicates)

    def getMaxOrder(self):
        rels = self. getPartRelations()
        if rels:
            return max(r.order for r in rels)
        return 1

    def getOrderForPosition(self, pos):
        rels = self. getPartRelations()
        if pos < 0:
            pos = len(rels) + pos
        previous = 0
        value = None
        for idx, r in enumerate(rels):
            if idx == pos:  # position found
                if previous < r.order - 1:  # space for a new entry
                    value = previous + 1
                    break
                value = r.order
                r.order += 1
            elif idx > pos:
                if previous < r.order - 1:  # no renumber necessary any more
                    break
                r.order += 1
            previous = r.order
        if value is None:  # pos was greater than length, use last order found
            value = previous + 1
        return value

    @Lazy
    def conceptManager(self):
        return self.context.getConceptManager()

    @Lazy
    def resourceManager(self):
        return self.getLoopsRoot().getResourceManager()

    @Lazy
    def partOf(self):
        return self.compoundPredicates[0]

