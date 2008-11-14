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
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName

from loops.browser.common import BaseView
from loops.interfaces import IResource
from loops import util


report_macros = ViewPageTemplateFile('report.pt')


class TrackingStats(BaseView):

    template = report_macros

    @Lazy
    def macro(self):
        return self.macros['report']

    @Lazy
    def macros(self):
        return self.template.macros

    @Lazy
    def accessRecords(self):
        return self.filter(reversed(self.loopsRoot.getRecordManager()['access'].values()))

    @Lazy
    def changeRecords(self):
        return self.filter(reversed(self.loopsRoot.getRecordManager()['changes'].values()))

    def filter(self, tracks):
        for tr in tracks:
            try:
                if IResource.providedBy(util.getObjectForUid(tr.taskId)):
                    yield tr
            except KeyError:
                pass

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

    def getObjectDetails(uid):
        """ Listing of last n accesses and changes of the object specified by
            the uid given.
        """


def formatAsMonth(d):
    return d.isoformat()[:7]