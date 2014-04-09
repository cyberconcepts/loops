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
Definition of view classes and other browser related stuff for comments.
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.security import checkPermission

from cybertools.browser.action import actions
from cybertools.tracking.btree import TrackingStorage
from loops.browser.action import DialogAction
from loops.browser.common import BaseView
from loops.browser.form import ObjectForm, EditObject
from loops.browser.node import NodeView
from loops.organize.comment.base import Comment
from loops.organize.party import getPersonForUser
from loops.organize.stateful.browser import StateAction
from loops.organize.tracking.report import TrackDetails
from loops.security.common import canAccessObject
from loops.setup import addObject
from loops import util
from loops.util import _


comment_macros = ViewPageTemplateFile('comment_macros.pt')


class CommentsView(NodeView):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @Lazy
    def allowed(self):
        if self.virtualTargetObject is None:
            return False
        opts = (self.globalOptions('organize.allowComments') or
                self.typeOptions('organize.allowComments'))
        if not opts:
            return False
        if opts is True:
            opts = []
        if self.isAnonymous and not 'all' in opts:
            return False
        return True

    @Lazy
    def addUrl(self):
        return '%s/create_comment.html' % self.virtualTargetUrl
        #return '%s/create_comment.html' % self.getUrlForTarget(self.context)

    @Lazy
    def addOnClick(self):
        self.registerDojoFormAll()
        return "objectDialog('createComment', '%s'); return false;" % self.addUrl

    def allItems(self):
        result = []
        rm = self.loopsRoot.getRecordManager()
        ts = rm.get('comments')
        target = self.virtualTargetObject
        if None in (ts, target):
            return result
        for tr in ts.query(taskId=util.getUidForObject(target)):
            result.append(CommentDetails(self, tr))
        return result

    def getActionsFor(self, comment):
        if not checkPermission('loops.ViewRestricted', self.context):
            return []
        trackUid = util.getUidForObject(comment.track)
        url = '%s/.%s/change_state.html' % (
                    self.page.virtualTargetUrl, trackUid)
        onClick = ("objectDialog('change_state', "
                    "'%s?dialog=change_state"
                    "&target_uid=%s'); return false;" % (url, trackUid))
        stateAct = StateAction(self, 
                        definition='organize.commentStates', 
                        stateful=comment.track,
                        url=url,
                        onClick=onClick)
        return [stateAct]


class CommentDetails(TrackDetails):

    @Lazy
    def poster(self):
        name = self.track.data.get('name')
        if name:
            return name
        return self.user['title']

    @Lazy
    def subject(self):
        return self.track.data['subject']

    @Lazy
    def text(self):
        return self.view.renderText(self.track.data['text'],
               self.track.contentType)


class CreateCommentForm(ObjectForm):

    template = comment_macros

    def checkPermissions(self):
        return canAccessObject(self.target)

    @Lazy
    def macro(self):
        return self.template.macros['create_comment']


class CreateComment(EditObject):

    def checkPermissions(self):
        return canAccessObject(self.target)

    @Lazy
    def personId(self):
        if self.view.isAnonymous:
            return self.request.form.get('email')
        p = getPersonForUser(self.context, self.request)
        if p is not None:
            return util.getUidForObject(p)
        return self.request.principal.id

    @Lazy
    def object(self):
        return self.view.virtualTargetObject

    def update(self):
        form = self.request.form
        subject = form.get('subject')
        text = form.get('text') or u''
        if not subject or self.personId is None or self.object is None:
            return True
        #contentType = form.get('contentType') or 'text/restructured'
        rm = self.view.loopsRoot.getRecordManager()
        ts = rm.get('comments')
        if ts is None:
            ts = addObject(rm, TrackingStorage, 'comments', trackFactory=Comment)
        uid = util.getUidForObject(self.object)
        data = dict(subject=subject, text=text)
        for k in ('name', 'email'):
            if k in form:
                data[k] = form[k]
        ts.saveUserTrack(uid, 0, self.personId, data)
        url = self.view.virtualTargetUrl + '?version=this'
        self.request.response.redirect(url)
        return False
