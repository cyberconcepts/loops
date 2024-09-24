# loops.organize.job.base

""" Base class(es) for job management.
"""

from zope import component, interface

from cybertools.organize.interfaces import IJobManager
from loops.interfaces import ILoops


@interface.implementer(IJobManager)
class JobManager(object):

    component.adapts(ILoops)

    view = None      # may be set by calling view

    def __init__(self, context):
        self.context = context

    def process(self):
        raise NotImplementedError("Method 'process' has to be implemented by subclass.")
