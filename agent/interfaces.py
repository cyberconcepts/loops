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
loops client agent interfaces.

$Id$
"""

from zope.interface import Interface, Attribute


class IAgent(Interface):
    """ An agent watches its client, looks for resources to process,
        and transfers these to its server.
    """


class IScheduler(Interface):
    """ Manages jobs and cares that they are started at the appropriate
        time.
    """

    logger = Attribute('Logger instance to be used for recording '
                       'job execution and execution results.')

    def schedule(job, startTime):
        """ Register the job given for execution at the intended start
            date/time.
        """

    def getJobsToExecute(startTime=None):
        """ Return a collection of jobs that are scheduled for execution at
            or before the date/time given.

            If startTime is None the current date/time is used.
        """


class IScheduledJob(Interface):
    """ A job that will be executed on some external triggering at
        a predefined date and time.
    """

    startTime = Attribute('Date/time at which the job should be executed.')
    params = Attribute('Mapping with key/value pairs to be passed to the '
                       'execute method call as keyword parameters.')

    def execute(**kw):
        """ Execute the job.

            Store log information about job execution in a log record.
        """

    def reschedule(startTime):
        """ Re-schedule the job, setting the date/time the job should be
            executed again.
        """


class ILogger(Interface):
    """ Collection of log records.
    """


class ILogRecord(Interface):
    """
    """


class ICrawler(Interface):
    """ Collects resources.
    """

    def collect(**criteria):
        """ Return a collection of resources that should be transferred
            the the server using the selection criteria given.
        """


class ITransporter(Interface):
    """ Transfers collected resources to the server. A resource need
        not be transferred immediately, resources may be be collected
        first and transferred later together, e.g. as a compressed file.
    """

    serverURL = Attribute('URL of the server the resources will be '
                          'transferred to. The URL also determines the '
                          'transfer protocol, e.g. HTTP or FTP.')
    method = Attribute('Transport method, e.g. PUT.')

    def transfer(resource, resourceType=file):
        """ Transfer the resource (typically just a file that may
            be read) to the server.
        """

    def commit():
        """ Transfer all resources not yet transferred.
        """


class IConfigurator(Interface):
    """ Manages (stores and receives) configuration information.
    """

    def loadConfiguration():
        """ Find the configuration settings and load them.
        """

    def getConfigOption(key):
        """ Return the value for the configuration option identified
            by the key given.
        """
