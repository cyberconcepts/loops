#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
Adapters for IConcept providing interfaces from the cybertools.organize package.

$Id$
"""

from time import mktime
from zope.component import adapts
from zope.interface import implements

from loops.organize.interfaces import ITask
from loops.interfaces import IConcept
from loops.interfaces import IIndexAttributes
from loops.common import AdapterBase
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (ITask,)


class Task(AdapterBase):
    """ typeInterface adapter for concepts of type 'task' or 'project'.
    """

    implements(ITask)

    _adapterAttributes = ('context', '__parent__',)
    _contextAttributes = list(ITask)


class IndexAttributes(object):

    implements(IIndexAttributes)
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

