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
Recording changes to loops objects.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.component import adapter

from cybertools.organize.work import WorkItem as BaseWorkItem
from cybertools.organize.work import WorkItems as BaseWorkItems
from loops.organize.tracking.base import BaseRecordManager


class WorkItem(BaseWorkItem):

    pass


class WorkItems(BaseRecordManager, BaseWorkItems):

    pass

