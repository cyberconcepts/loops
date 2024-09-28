# loops.organize.job.browser

""" Definition of view classes and other browser related stuff for job management.
"""

from logging import getLogger
from zope import component
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy

from cybertools.meta.interfaces import IOptions
from cybertools.organize.interfaces import IJobManager


class Executor(object):
    """ A view whose processJobs method should be called via cron + wget
        in order to execute all jobs that are found.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @Lazy
    def options(self):
        return IOptions(self.context)

    @Lazy
    def logger(self):
        return getLogger('loops.organize.job')

    def processJobs(self):
        output = []
        names = [n for n in self.request.get('job_managers', '').split(',') 
                    if n]
        if not names:
            names = self.options('organize.job.managers', [])
        for name in names:
            manager = component.queryAdapter(self.context, IJobManager, 
                                             name=name)
            if manager is None:
                msg = "Job manager '%s' not found." % name
                self.logger.warning(msg)
                output.append(msg)
            else:
                manager = removeSecurityProxy(manager)
                manager.view = self
                output.append(manager.process())
        if not output:
            return 'No job managers available.'
        return '\n'.join(m for m in output if m)
