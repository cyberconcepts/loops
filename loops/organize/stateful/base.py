# loops.organize.stateful.base

""" Basic implementations for stateful objects and adapters.
"""

from zope.catalog.interfaces import ICatalog
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts, adapter

from cybertools.composer.schema.field import Field
from cybertools.meta.interfaces import IOptions
from cybertools.stateful.base import Stateful as BaseStateful
from cybertools.stateful.base import StatefulAdapter, IndexInfo
from cybertools.stateful.interfaces import IStatesDefinition, ITransitionEvent
from loops.common import adapted
from loops.interfaces import ILoopsObject, IConcept, IResource
from loops import util
from loops.util import _


class Stateful(BaseStateful):

    def getStatesDefinition(self):
        return component.getUtility(IStatesDefinition, self.statesDefinition)


class StatefulLoopsObject(Stateful, StatefulAdapter):

    adapts(ILoopsObject)

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def typePredicate(self):
        return self.loopsRoot.getConceptManager().getTypePredicate()

    @Lazy
    def adapted(self):
        return adapted(self.context)


class SimplePublishable(StatefulLoopsObject):

    statesDefinition = 'simple_publishing'


class StatefulConceptIndexInfo(IndexInfo):

    adapts(IConcept)

    @property
    def availableStatesDefinitions(self):
        globalOptions = IOptions(self.context.getLoopsRoot())
        type = self.context.conceptType
        if type is None:    # may happen during object creation
            return globalOptions('organize.stateful.concept', [])
        else:
            typeOptions = IOptions(adapted(type))
            return (globalOptions('organize.stateful.concept', []) +
                    typeOptions('organize.stateful', []))


class StatefulResourceIndexInfo(IndexInfo):

    adapts(IResource)

    @property
    def availableStatesDefinitions(self):
        options = IOptions(self.context.getLoopsRoot())
        return options('organize.stateful.resource', ())


@adapter(IResource, ITransitionEvent)
def handleTransition(obj, event):
    previous = event.previousState
    next = event.transition.targetState
    if next != previous:
        cat = component.getUtility(ICatalog)
        cat.index_doc(int(util.getUidForObject(obj)), obj)


# predefined fields for transition forms

commentsField = Field('comments', _(u'label_transition_comments'), 'textarea', 
                      description=_(u'desc_transition_comments'), 
                      nostore=True)
