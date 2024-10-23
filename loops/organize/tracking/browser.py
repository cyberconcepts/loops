# loops.organize.tracking.browser

""" View classes for tracks.
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName

from cybertools.browser.action import actions
from cybertools.tracking.browser import TrackView
from loops.browser.action import DialogAction
from loops.browser.form import ObjectForm, EditObject
from loops.organize.party import getPersonForUser
from loops import util

track_edit_template = ViewPageTemplateFile('edit_track.pt')


class BaseTrackView(TrackView):

    @Lazy
    def task(self):
        uid = self.metadata['taskId']
        return util.getObjectForUid(uid)

    @Lazy
    def taskTitle(self):
        task = self.task
        if task is None:
            return self.metadata['taskId']
        return getattr(task, 'title', None) or getName(task)

    @Lazy
    def taskUrl(self):
        task = self.task
        if task is not None:
            return '%s/@@SelectedManagementView.html' % absoluteURL(task, self.request)

    @Lazy
    def user(self):
        uid = self.metadata['userName']
        if uid.isdigit():
            obj = util.getObjectForUid(uid)
            if obj is not None:
                return obj
        result = []
        for id in uid.split('.'):
            if id.isdigit():
                obj = util.getObjectForUid(id)
                if obj is not None:
                    result.append(obj.title)
                    continue
            result.append(id)
        return ' / '.join(result)

    @Lazy
    def authentication(self):
        return component.getUtility(IAuthentication)

    @Lazy
    def userTitle(self):
        if isinstance(self.user, str):
            uid = self.user
            try:
                return self.authentication.getPrincipal(uid).title or uid
            except PrincipalLookupError:
                return uid
        return self.user.title

    @Lazy
    def userUrl(self):
        user = self.user
        if user is not None and not isinstance(user, str):
            return '%s/@@introspector.html' % absoluteURL(user, self.request)

    def getMetadataTarget(self, key):
        value = self.metadata.get(key)
        if value is not None and (isinstance(value, int) or value.isdigit()):
            obj = util.getObjectForUid(value)
            if obj is not None:
                url = ('%s/@@SelectedManagementView.html' %
                                        absoluteURL(obj, self.request))
                return dict(title=obj.title, url=url, obj=obj)
        return dict(title=value, url=None, obj=None)

    @Lazy
    def personId(self):
        p = getPersonForUser(self.context, self.request)
        if p is not None:
            return util.getUidForObject(p)
        return self.request.principal.id


class EditForm(BaseTrackView):

    template = track_edit_template

    def update(self):
        form = self.request.form
        if not form.get('form_submitted'):
            return True
        data = {}
        for row in form.get('data') or []:
            key = row['key']
            if not key:
                continue
            value = row['value']
            # TODO: unmarshall value if necessary
            data[key] = value
        context = removeSecurityProxy(self.context)
        context.data = data
        return True


# specialized views

class ChangeView(BaseTrackView):

    pass


class AccessView(BaseTrackView):

    pass

