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
View class(es) for accessing tasks and work items as meeting minutes.
"""

from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import actions
from cybertools.docgen.base import WordDocument
from loops.browser.action import TargetAction
from loops.expert.browser.report import ResultsConceptView
from loops.util import _


meeting_template = ViewPageTemplateFile('meeting.pt')


actions.register('meeting_minutes', 'portlet', TargetAction,
        title=_(u'Show Meeting Minutes...'),
        description=_(u'Show meeting minutes for this object.'),
        viewName='meeting_minutes.html',
)

class MeetingMinutes(ResultsConceptView):

    reportName = 'meeting_minutes'
    reportDownload = 'meeting_minutes.doc'

    @Lazy
    def meeting_macros(self):
        return meeting_template.macros

    @Lazy
    def macro(self):
        return self.meeting_macros['content']

    @Lazy
    def resultsRenderer(self):
        return self.meeting_macros['results']

    def getColumnRenderer(self, col):
        renderer = col.renderer
        if renderer == 'subreport':
            return self.meeting_macros[renderer]
        return self.result_macros[renderer]


class MeetingMinutesDocument(WordDocument, MeetingMinutes):

    isToplevel = True
    omitSectionElement = True

    def __init__(self, context, request):
        MeetingMinutes.__init__(self, context, request)

    def __call__(self, *args, **kw):
        return self.embed(*args, **kw)

    @Lazy
    def macros(self):
        return meeting_template.macros

    @Lazy
    def reportRenderer(self):
        return self.macros['document']

    @Lazy
    def content(self):
        return self.reportRenderer


