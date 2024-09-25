# loops.organize.task

""" Adapters for IConcept providing interfaces from the 
cybertools.organize package.
"""

from time import mktime
from zope.component import adapts
from zope.interface import implementer

from loops.organize.interfaces import ITask, IEvent, IAgendaItem
from loops.interfaces import IConcept
from loops.interfaces import IIndexAttributes
from loops.common import AdapterBase
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (ITask, IEvent, IAgendaItem)


@implementer(ITask)
class Task(AdapterBase):
    """ typeInterface adapter for concepts of type 'task' or 'project'.
    """

    _adapterAttributes = AdapterBase._adapterAttributes
    _contextAttributes = list(ITask)


@implementer(IEvent)
class Event(Task):
    """ A scheduled event or appointment.
    """

    _contextAttributes = list(IEvent)


@implementer(IAgendaItem)
class AgendaItem(AdapterBase):
    """ Some topic (a sort of task) that is discussed during an event.
    """

    _contextAttributes = list(IAgendaItem)


@implementer(IIndexAttributes)
class IndexAttributes(object):

    adapts(ITask)

    def __init__(self, context):
        self.context = context

    def text(self):
        # TODO: collect text from work items
        return ' '.join((self.title, self.description))

    def date(self):
        value = self.context.start
        if value:
            return int(mktime(value.utctimetuple))

