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

    scheduler = Attribute('IScheduler instance')


class IScheduler(Interface):
    """ Manages jobs and cares that they are started at the appropriate
        time.
    """

    logger = Attribute('Logger instance to be used for recording '
                       'job execution and execution results.')

    def schedule(job, startTime):
        """ Register the job given for execution at the intended start
            date/time and return the job.
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
    successors = Attribute('Jobs to execute immediately after this '
                           'one has been finished.')

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


class ICrawlingJob(IScheduledJob):
    """ Collects resources.
    """

    predefinedMetadata = Attribute('A mapping with metadata to be used '
                                   'for all resources found.')

    def collect(**criteria):
        """ Return a deferred that upon callback will provide a
            collection of resource/metadata pairs that should be transferred
            to the server.

            Use the selection criteria given to filter the resources that
            should be collected.
        """


class IResource(Interface):
    """ Represents a data object that is collected by a crawler and
        will be transferred to the server.
    """

    data = Attribute("A string, file, or similar representation of the "
                     "resource's content")


class IMetadataSet(Interface):
    """ Metadata associated with a resource.
    """

    def asXML():
        """ Return an XML string representing the metadata set.

            If this metadata set contains other metadata sets
            (nested metadata) this will be converted to XML as well.
        """

    def setData(key, value):
        """ Set a metadata element.

            The value may be a string or another metadata set
            (nested metadata).
        """


class ITransporter(Interface):
    """ Transfers collected resources to the server.
    """

    serverURL = Attribute('URL of the server the resources will be '
                          'transferred to. The URL also determines the '
                          'transfer protocol, e.g. HTTP or FTP.')
    method = Attribute('Transport method, e.g. PUT.')
    machineName = Attribute('Name under which the local machine is '
                            'known to the server.')
    userName = Attribute('User name for logging in to the server.')
    password = Attribute('Password for logging in to the server.')

    def transfer(resource, metadata=None, resourceType=file):
        """ Transfer the resource (typically just a file that may
            be read) to the server.

            The resource may be associated with a metadata set.
        """


class ITransportJob(IScheduledJob):
    """ A job managing the the transfer of a resource to the server.
    """

    transporter = Attribute('The transporter object to use for transer.')


class IConfigurator(Interface):
    """ Manages (stores and receives) configuration information.
    """

    def loadConfiguration():
        """ Find the configuration settings and load them.
        """

    def setConfigOption(key, value):
        """ Directly set a certain configuration option.
        """

    def getConfigOption(key):
        """ Return the value for the configuration option identified
            by the key given.

            In addition config options must be directly accessible
            via attribute notation.
        """


class IPackageManager(Interface):
    """ Allows to install, update, or remove software packages (plugins,
        typically as Python eggs) from a server.
    """

    sources = Attribute('A list of URLs that provide software packages. ')

    def getInstalledPackages():
        """ Return a list of dictionaries, format:
            [{'name': name, 'version': version,
              'date': date_time_of_installation,}, ...]
        """

    def getUpdateCandidates():
        """ Return a list of dictionaries with information about updateable
            packages.
        """

    def installPackage(name, version=None, source=None):
        """ Install a package.
            If version is not given try to get the most recent one.
            If source is not given search the sources attribute for the
            first fit.
        """

    def updatePackage(name, version=None, source=None):
        """ Update a package.
            If version is not given try to get the most recent one.
            If source is not given search the sources attribute for the
            first fit.
        """

    def removePackage(name):
        """ Remove a package from this agent.
        """
