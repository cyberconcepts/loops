#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
loops standard reports.
"""

from zope.cachedescriptors.property import Lazy

from cybertools.util.jeep import Jeep
from loops.browser.concept import ConceptView
from loops.expert.field import Field, TargetField, DateField, StateField, \
                            TextField, HtmlTextField, UrlField
from loops.expert.report import ReportInstance


title = UrlField('title', u'Title',
                description=u'A short descriptive text.',
                executionSteps=['output'])


class TypeInstances(ReportInstance):

    fields = Jeep((title,))
    defaultOutputFields = fields

    @Lazy
    def targets(self):
        targetPredicate = self.view.conceptManager['querytarget']
        return self.view.context.getChildren([targetPredicate])

    def selectObjects(self, parts):
        result = []
        for t in self.targets:
            for c in t.getChildren([self.view.typePredicate]):
                result.append(c)
        print '***', self.targets, result
        return result

