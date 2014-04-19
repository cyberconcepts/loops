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
Report views and definitions for comments listings and similar stuff.
"""

from cybertools.util.jeep import Jeep
from loops.expert.browser.report import ReportConceptView
from loops.expert.field import Field, StateField, TargetField
from loops.expert.field import TrackDateField
from loops.expert.report import ReportInstance, TrackRow


class CommentsOverview(ReportConceptView):

    reportName = 'comments_overview'


timeStamp = TrackDateField('timeStamp', u'Timestamp',
                description=u'The date and time the comment was posted.',
                part='dateTime', descending=True,
                executionSteps=['sort', 'output'])
target = TargetField('taskId', u'Target',
                description=u'The resource or concept the comment was posted at.',
                executionSteps=['output'])
name = Field('name', u'Name',
                description=u'The name addres of the poster.',
                executionSteps=['output'])
email = Field('email', u'E-Mail Address',
                description=u'The email addres of the poster.',
                executionSteps=['output'])
subject = Field('subject', u'Subject',
                description=u'The subject of the comment.',
                executionSteps=['output'])
state = StateField('state', u'State',
                description=u'The state of the comment.',
                cssClass='center',
                statesDefinition='organize.commentStates',
                executionSteps=['query', 'sort', 'output'])


class CommentsRow(TrackRow):

    pass


class CommentsReportInstance(ReportInstance):

    type = "comments_overview"
    label = u'Comments Overview'

    rowFactory = CommentsRow

    fields = Jeep((timeStamp, target, name, email, subject, state))
    defaultOutputFields = fields
    defaultSortCriteria = (state, timeStamp)

    def selectObjects(self, parts):
        return self.recordManager['comments'].values()
