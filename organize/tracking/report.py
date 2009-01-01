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
Adapter and view class(es) for statistics reporting.

$Id$
"""

from datetime import date, datetime
from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.cachedescriptors.property import Lazy
from zope.interface.interface import InterfaceClass
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName

from cybertools.meta.interfaces import IOptions
from cybertools.util import format
from loops.browser.common import BaseView
from loops.interfaces import IConcept, IResource
from loops import util
from loops.util import _
from loops.versioning.interfaces import IVersionable


report_macros = ViewPageTemplateFile('report.pt')


class TrackingStats(BaseView):

    template = report_macros

    typeMapping = {'resource:*': IResource, 'concept:*': IConcept}

    @Lazy
    def macro(self):
        return self.macros['report']

    @Lazy
    def macros(self):
        return self.template.macros

    @Lazy
    def options(self):
        return IOptions(self.adapted)

    @Lazy
    def typeNames(self):
        return self.options('types') or ['resource:*']

    @Lazy
    def accessRecords(self):
        return self.filter(reversed(self.loopsRoot.getRecordManager()['access'].values()))

    @Lazy
    def changeRecords(self):
        return self.filter(reversed(self.loopsRoot.getRecordManager()['changes'].values()))

    def filter(self, tracks):
        for tr in tracks:
            try:
                if self.checkType(util.getObjectForUid(tr.taskId)):
                    yield tr
            except KeyError:
                pass

    @Lazy
    def typeObjects(self):
        result = []
        for tn in self.typeNames:
            ifc = self.typeMapping.get(tn)
            if ifc is None:
                tp = self.conceptManager.get(tn)
                if tp is not None:
                    result.append(tp)
            else:
                result.append(ifc)
        return result

    def checkType(self, obj):
        if not IResource.providedBy(obj) and not IConcept.providedBy(obj):
            return False
        for t in self.typeObjects:
            if isinstance(t, InterfaceClass):
                if t.providedBy(obj):
                    return True
            elif obj.getType() == t:
                    return True
        return False

    def getData(self):
        form = self.request.form
        period = form.get('period')
        uid = form.get('id')
        if period is not None:
            result = self.getPeriodDetails(period)
            macroName = 'period'
        elif uid is not None:
            result = self.getObjectDetails(uid)
            macroName = 'object'
        else:
            result = self.getOverview()
            macroName = 'overview'
        macro = self.macros[macroName]
        return dict(data=result, macro=macro)

    def getOverview(self):
        """ Period-based (monthly) listing of the numbers of object accesses, new,
            changed, [deleted] objects, number of resources at end of month.
        """
        periods = {}
        for track in self.accessRecords:
            ts = datetime.fromtimestamp(track.timeStamp)
            p = date(ts.year, ts.month, 1)
            periods.setdefault(p, dict(access=0, new=0, changed=0))
            periods[p]['access'] += 1
        for track in self.changeRecords:
            ts = datetime.fromtimestamp(track.timeStamp)
            p = date(ts.year, ts.month, 1)
            periods.setdefault(p, dict(access=0, new=0, changed=0))
            #periods[p]['new'] += 1
            if track.data['action'] == 'modify':
                periods[p]['changed'] += 1
            elif track.data['action'] == 'add':
                periods[p]['new'] += 1
        result = [dict(period=formatAsMonth(p), **periods[p])
                    for p in reversed(sorted(periods))]
        num = len(self.resourceManager)
        for data in result:
            data['count'] = num
            num = num - data['new']
        return result

    def getPeriodDetails(period):
        """ Listing of accessed, new, changed, [deleted] objects during
            the period given.
        """

    def getObjectDetails(uid, period=None):
        """ Listing of (last n?) accesses and changes of the object specified by
            the uid given, optionally limited to the period (month) given.
        """


class RecentChanges(TrackingStats):

    def getData(self):
        sizeOption = self.options('size')
        size = int(self.request.form.get('size') or
                   (sizeOption and sizeOption[0]) or 15)
        new = {}
        changed = {}
        result = []
        for track in self.changeRecords:
            if len(result) >= size:
                break
            if track.data['action'] == 'add' and track.taskId not in new:
                sameChanged = changed.get(track.taskId)
                if sameChanged and sameChanged.timeStamp < track.timeStamp + 60:
                    # skip change immediate after creation
                    if result[-1].taskId == track.taskId:
                        result.pop()
                new[track.taskId] = track
                result.append(track)
                continue
            if track.data['action'] == 'modify' and track.taskId not in changed:
                changed[track.taskId] = track
                result.append(track)
                continue
        return dict(data=[TrackDetails(self, tr) for tr in result],
                    macro=self.macros['recent_changes'])


class TrackDetails(BaseView):

    timeStampFormat = 'short'

    def __init__(self, view, track):
        self.view = view
        self.track = track

    @Lazy
    def month(self):
        ts = datetime.fromtimestamp(self.track.timeStamp)
        return formatAsMonth(date(ts.year, ts.month, 1))

    @property
    def monthChanged(self):
        result = self.view.lastMonth != self.month
        self.view.lastMonth = self.month
        return result

    @Lazy
    def authentication(self):
        return component.getUtility(IAuthentication)

    @Lazy
    def object(self):
        return util.getObjectForUid(self.track.taskId)

    @Lazy
    def context(self):
        return self.object

    @Lazy
    def objectData(self):
        obj = self.object
        node = self.view.nodeView
        url = node is not None and node.getUrlForTarget(obj) or ''
        versionable = IVersionable(self.object, None)
        version = versionable is not None and versionable.versionId or ''
        return dict(object=obj, title=obj.title,
                    type=self.longTypeTitle, url=url, version=version)

    @Lazy
    def user(self):
        userName = self.track.userName
        obj = util.getObjectForUid(userName)
        if obj is None:
            try:
                userTitle = self.authentication.getPrincipal(userName).title
            except PrincipalLookupError:
                userTitle = userName
            return dict(object=None, title=userTitle, url='')
        node = self.view.nodeView
        url = node is not None and node.getUrlForTarget(obj) or ''
        return dict(object=obj, title=obj.title, url=url)

    @Lazy
    def action(self):
        return self.track.data.get('action', '')

    @Lazy
    def markNew(self):
        return self.action == 'add' and '*' or ''

    @Lazy
    def timeStamp(self):
        return self.formatTimeStamp(self.track.timeStamp)
        #value = datetime.fromtimestamp(self.track.timeStamp)
        #return format.formatDate(value, 'dateTime', self.timeStampFormat,
        #                         self.view.languageInfo.language)

    def formatTimeStamp(self, ts):
        if not ts:
            return u''
        value = datetime.fromtimestamp(ts)
        return format.formatDate(value, 'dateTime', self.timeStampFormat,
                                 self.view.languageInfo.language)

    def __repr__(self):
        return repr(self.track)


def formatAsMonth(d):
    return d.isoformat()[:7]
