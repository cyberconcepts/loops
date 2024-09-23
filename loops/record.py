#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Definition of the View and related classses.

$Id$
"""

from zope.app.container.btree import BTreeContainer
from zope.interface import implements
from zope.traversing.api import getParent

from cybertools.util.jeep import Jeep
from loops.interfaces import ILoopsContained
from loops.interfaces import IRecordManager


class RecordManager(BTreeContainer):

    implements(IRecordManager, ILoopsContained)

    title = 'records'

    def getLoopsRoot(self):
        return getParent(self)

    def getAllParents(self, collectGrants=False):
        return Jeep()

