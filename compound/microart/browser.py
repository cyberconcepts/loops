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

from loops.browser.concept import ConceptView, ConceptRelationView
from loops.common import adapted
from loops import util
from loops.util import _


view_macros = ViewPageTemplateFile('view_macros.pt')


class MicroArtView(ConceptView):

    @Lazy
    def macro(self):
        return view_macros.macros['microart']

    def render(self):
        return self.renderText(self.data['text'], self.adapted.textContentType)

    def resources(self):
        stdPred = self.loopsRoot.getConceptManager().getDefaultPredicate()
        rels = self.context.getResourceRelations([stdPred])
        for r in rels:
            yield self.childViewFactory(r, self.request, contextIsSecond=True)

