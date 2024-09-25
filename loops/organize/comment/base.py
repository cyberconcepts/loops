# loops.organize.comment.base

""" Base classes for comments/discussions.
"""

from zope.component import adapts
from zope.interface import implementer
from zope.traversing.api import getParent

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
        State('rejected', 'rejected', ('accept',), color='grey'),
        Transition('accept', 'accept', 'public'),
        Transition('reject', 'reject', 'rejected'),
        Transition('retract', 'retract', 'new'),
        initialState='new')


@implementer(IComment)
class Comment(Stateful, Track):

    metadata_attributes = Track.metadata_attributes + ('state',)
    index_attributes = metadata_attributes
    typeName = 'Comment'
    typeInterface = IComment
    statesDefinition = 'organize.commentStates'

    contentType = 'text/restructured'

    def __init__(self, taskId, runId, userName, data):
        super(Comment, self).__init__(taskId, runId, userName, data)
        self.state = self.getState()    # make initial state persistent

    @property
    def title(self):
        return self.data['subject']

    def doTransition(self, action):
        super(Comment, self).doTransition(action)
        getParent(self).indexTrack(None, self, 'state')

