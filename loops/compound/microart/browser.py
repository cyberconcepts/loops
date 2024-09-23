#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
View classes for micro articles (MicroArt).
"""


import itertools
from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from loops.browser.action import actions, DialogAction
from loops.browser.concept import ConceptView
from loops.common import adapted
from loops import util
from loops.util import _


actions.register('create_microart', 'portlet', DialogAction,
        title=_(u'Create MicroArticle...'),
        description=_(u'Create a new MicroArticle.'),
        viewName='create_concept.html',
        dialogName='createConcept',
        typeToken='.loops/concepts/microart',
        fixedType=True,
        #prerequisites=['registerDojoTextWidget'],
)

actions.register('edit_microart', 'portlet', DialogAction,
        title=_(u'Edit MicroArticle...'),
        description=_(u'Modify MicroArticle.'),
        viewName='edit_concept.html',
        dialogName='editConcept',
        #prerequisites=['registerDojoTextWidget'],
)


view_macros = ViewPageTemplateFile('view_macros.pt')


class MicroArtView(ConceptView):

    @Lazy
    def contentType(self):
        return 'text/restructured'

    @Lazy
    def macros(self):
        return self.controller.getTemplateMacros('microart.view', view_macros)

    @Lazy
    def macro(self):
        return self.macros['main']

    @Lazy
    def story(self):
        return self.renderText(self.adapted.story, self.contentType)

    @Lazy
    def insight(self):
        return self.renderText(self.adapted.insight, self.contentType)

    @Lazy
    def consequences(self):
        return self.renderText(self.adapted.consequences, self.contentType)

    @Lazy
    def followUps(self):
        return self.renderText(self.adapted.followUps, self.contentType)

