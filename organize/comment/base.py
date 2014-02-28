#
#  Copyright (c) 2014 Helmut Merz helmutm@cy55.de
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
Base classes for comments/discussions.
"""

from zope.component import adapts
from zope.interface import implementer, implements

from cybertools.stateful.definition import StatesDefinition
from cybertools.stateful.definition import State, Transition
from cybertools.stateful.interfaces import IStatesDefinition
from cybertools.tracking.btree import Track
from cybertools.tracking.interfaces import ITrackingStorage
from loops.organize.comment.interfaces import IComment
from loops.organize.stateful.base import Stateful
from loops import util


@implementer(IStatesDefinition)
def commentStates():
    return StatesDefinition('commentStates',
        State('new', 'new', ('accept', 'reject'), color='red'),
        State('public', 'public', ('retract', 'reject'), color='green'),
        State('rejected', 'rejected', ('accept'), color='grey'),
        Transition('accept', 'accept', 'public'),
        Transition('reject', 'reject', 'rejected'),
        Transition('retract', 'retract', 'new'),
        initialState='new')


class Comment(Stateful, Track):

    implements(IComment)

    metadata_attributes = Track.metadata_attributes + ('state',)
    index_attributes = metadata_attributes
    typeName = 'Comment'
    typeInterface = IComment
    statesDefinition = 'organize.commentStates'

    contentType = 'text/restructured'

    def __init__(self, taskId, runId, userName, data):
        super(Comment, self).__init__(taskId, runId, userName, data)
        self.state = self.getState()    # make initial state persistent

