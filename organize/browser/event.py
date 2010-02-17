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
Definition of view classes and other browser related stuff for tasks.

$Id$
"""

import calendar
from datetime import date, datetime, timedelta
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.meta.interfaces import IOptions
from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.common import adapted
from loops.util import _


organize_macros = ViewPageTemplateFile('view_macros.pt')


class BaseEvents(object):

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
        return sorted((rv for rv in relViews
                          if not rv.adapted.end or
                             rv.adapted.end >= now - timedelta(delta)),
                      key=sort)


class Events(ConceptView, BaseEvents):

    @Lazy
    def macro(self):
        return organize_macros.macros['events']

    def getActions(self, category='object', page=None, target=None):
        actions = []
        if category == 'portlet':
            actions.append(DialogAction(self, title=_(u'Create Event...'),
                  description=_(u'Create a new event.'),
                  viewName='create_concept.html',
                  dialogName='createEvent',
                  typeToken='.loops/concepts/event',
                  fixedType=True,
                  innerForm='inner_concept_form.html',
                  page=page,
                  target=target))
            self.registerDojoDateWidget()
        return actions


class CalendarInfo(BaseEvents):

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

    def getEvents(self, day):
        if not day:
            return False
        d = datetime(self.selectedYear, self.selectedMonth, day)
        return []

