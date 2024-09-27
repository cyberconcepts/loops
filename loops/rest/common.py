# loops.rest.common

""" Common stuff for REST (REpresentational State Transfer) views.
"""

from zope.interface import implementer
from zope.component import adapts
from zope.publisher.interfaces.browser import IBrowserRequest, IBrowserPublisher

from loops.interfaces import IConcept

# interfaces

class IRESTView(IBrowserPublisher):
    """ The basic interface for all REST views.
    """

    def __call__():
        """ Render the representation.
        """


@implementer(IRESTView)
class ConceptView(object):
    """ A REST view for a concept.
    """

    adapts(IConcept, IBrowserRequest)

    def __init__(self, context, request):
        self.context = self.__parent__ = context
        self.request = request

    def __call__(self):
        return 'Hello REST'

    def browserDefault(self, request):
        """ Make the publisher happy.
        """
        return self, ()
