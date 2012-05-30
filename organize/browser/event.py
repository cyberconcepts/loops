#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
Definition of view classes and other browser related stuff for tasks.
"""

import calendar
from datetime import date, datetime, timedelta
from urllib import urlencode
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import actions
from cybertools.meta.interfaces import IOptions
from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.common import adapted
from loops.util import _


organize_macros = ViewPageTemplateFile('view_macros.pt')


actions.register('createEvent', 'portlet', DialogAction,
        title=_(u'Create Event...'),
        description=_(u'Create a new event.'),
        viewName='create_concept.html',
        dialogName='createEvent',
        typeToken='.loops/concepts/event',
        fixedType=True,
        prerequisites=['registerDojoDateWidget'],
)


class Events(ConceptView):

    @Lazy
    def macro(self):
        return organize_macros.macros['events']

    def getActions(self, category='object', page=None, target=None):
        acts = super(Events, self).getActions(category, page, target)
        if category == 'portlet':
            acts.extend(actions.get(category, ['createEvent'],
                                view=self, page=page, target=target))
        return acts

    @Lazy
    def selectedDate(self):
        year = int(self.request.get('cal_year') or 0)
        month = int(self.request.get('cal_month') or 0)
        day = int(self.request.get('cal_day') or 0)
        if year and month and day:
            return date(year, month, day)
        return None

    def events(self):
        cm = self.loopsRoot.getConceptManager()
        tEvent = cm['event']
        hasType = cm.getTypePredicate()
        now = datetime.today()
        delta = int(self.request.get('delta',
                        IOptions(adapted(self.context))('delta', [0])[0]))
        sort = lambda x: x.adapted.start or now
        relViews = (self.childViewFactory(r, self.request, contextIsSecond=True)
                        for r in tEvent.getChildRelations([hasType], sort=None))
        if self.selectedDate:
            #end = self.selectedDate + timedelta(1)
            return sorted((rv for rv in relViews
                                if rv.adapted.start.date() <= self.selectedDate and
                                   rv.adapted.end.date() >= self.selectedDate),
                        key=sort)
        else:
            return sorted((rv for rv in relViews
                            if not rv.adapted.end or
                                rv.adapted.end >= now - timedelta(delta)),
                        key=sort)


class CalendarInfo(NodeView):

    monthNames = ('January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December')

    weekDays = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @Lazy
    def today(self):
        return date.today()

    @Lazy
    def selectedYear(self):
        return int(self.request.get('cal_year') or self.today.year)

    @Lazy
    def selectedMonth(self):
        return int(self.request.get('cal_month') or self.today.month)

    @Lazy
    def previousYear(self):
        return self.selectedYear - 1

    @Lazy
    def nextYear(self):
        return self.selectedYear + 1

    @Lazy
    def previousMonth(self):
        m = self.selectedMonth
        y = self.selectedYear
        if m == 1:
            y, m = y - 1, 12
        else:
            m -= 1
        return dict(year=y, month=m)

    @Lazy
    def nextMonth(self):
        m = self.selectedMonth
        y = self.selectedYear
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        return dict(year=y, month=m)

    @Lazy
    def monthCalendar(self):
        return calendar.monthcalendar(self.selectedYear, self.selectedMonth)

    def isToday(self, day):
        if not day:
            return False
        return date(self.selectedYear, self.selectedMonth, day) == self.today

    def getWeekNumber(self, week):
        for day in week:
            if day:
                break
        return datetime(self.selectedYear, self.selectedMonth, day).isocalendar()[1]

    @Lazy
    def eventListQuery(self):
        calOption = self.globalOptions('organize.showCalendar')
        if isinstance(calOption, list):
            qu = self.conceptManager.get(calOption[0])
            return Events(qu, self.request)
        return None

    @Lazy
    def events(self):
        eventList = [[] for i in range(31)]
        cm = self.loopsRoot.getConceptManager()
        tEvent = cm['event']
        hasType = cm.getTypePredicate()
        start = datetime(self.selectedYear, self.selectedMonth, 1)
        fday, ndays = calendar.monthrange(self.selectedYear, self.selectedMonth)
        end = start + timedelta(ndays)
        view = self.eventListQuery
        if view is not None:
            relViews = (view.childViewFactory(r, self.request, contextIsSecond=True)
                            for r in tEvent.getChildRelations([hasType], sort=None))
            events = sorted((rv for rv in relViews
                            #if rv.adapted.start >= start and rv.adapted.start < end),
                            if rv.adapted.end >= start and rv.adapted.start <= end),
                        key=lambda x: (x.adapted.start, x.adapted.end))
            for ev in events:
                startDay = ev.adapted.start.day
                if ev.adapted.start < start:
                    startDay = 1
                endDay = ev.adapted.end.day
                if ev.adapted.end > end:
                    endDay = 31
                for d in range(startDay, endDay+1):
                    eventList[d-1].append(ev)
        return eventList

    def getEventsUrl(self, day):
        v = self.eventListQuery
        if v is not None:
            baseUrl = self.getUrlForTarget(v)
            params = dict(cal_year=self.selectedYear, cal_month=self.selectedMonth,
                          cal_day=day)
            return '?'.join((baseUrl, urlencode(params)))

    def getCssClass(self, day, tag='td'):
        if not day:
            return ''
        classes = []
        if tag == 'td':
            if self.isToday(day):
                classes.append('today')
            if self.events[day-1]:
                classes.append('has_events')
        return ' '.join(classes)

    def getEventTitles(self, day):
        events = self.events[day-1]
        return '; '.join(ev.title for ev in events)
