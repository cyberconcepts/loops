#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
System management interfaces.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from cybertools.tracking.interfaces import ITrack
from loops.interfaces import IConceptSchema
from loops.util import _


class IJobRecords(Interface):

    def recordExecution(job, state, transcript, data=None):
        """ Record the execution of a job (which may be a query or some other
            kind of concept).
        """

    def getLastRecordFor(job):
        """ Use this for finding out when the job given has been run
            most recently.
        """


class IJobRecord(ITrack):

    pass


# agent-based job control - not used at the moment.

class IJob(IConceptSchema):
    """ Specifies/represents a job to be executed by a cybertools.agent
        instance.
    """

    identifier = schema.TextLine(
                    title=_(u'Job Identifier'),
                    description=_(u'A name/ID unique within the realm of the '
                       'controller.'),
                   required=True,)
    agentId = schema.TextLine(
                    title=_(u'Agent Identifier'),
                    description=_(u'The identifier of the agent that will '
                        'execute the job; this identifies also the type '
                        'of job, e.g. a crawling or transport job.'),
                    required=False,)
    startTime = schema.Date(
                    title=_(u'Start Date/Time'),
                    description=_(u'Date/time at which the job should be '
                        'executed. If omitted the job will be executed '
                        'immediately.'),
                    required=False,)

    #params = Attribute('Mapping with key/value pairs to be used by '
    #                   'the ``execute()`` method.')
    #repeat = Attribute('Number of seconds after which the job should be '
    #                   'rescheduled. Do not repeat if 0.')
    #successors = Attribute('Jobs to execute immediately after this '
    #                   'one has been finished.')


class IJobManager(IConceptSchema):
    """ A container/manager for jobs to be executed by a cybertools.agent
        instance.
    """

