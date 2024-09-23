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
Automatic setup of a loops site for the organize.personal package.

$Id$
"""

from zope.component import adapts
from zope.interface import implements, Interface

from cybertools.tracking.btree import TrackingStorage
from loops.organize.personal.favorite import Favorite
from loops.organize.personal.filter import Filter
from loops.setup import SetupManager as BaseSetupManager


class SetupManager(BaseSetupManager):

    def setup(self):
        records = self.context.getRecordManager()
        favorites = self.addObject(records, TrackingStorage, 'favorites',
                                   trackFactory=Favorite)
        filters = self.addObject(records, TrackingStorage, 'filters',
                                   trackFactory=Filter)
