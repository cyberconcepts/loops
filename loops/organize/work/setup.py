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
Automatic setup of a loops site for the organize.work package.

$Id$
"""

from cybertools.tracking.btree import TrackingStorage
from loops.organize.work.base import WorkItem
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        records = self.context.getRecordManager()
        if 'work' not in records:
            records['work'] = TrackingStorage(trackFactory=WorkItem)
