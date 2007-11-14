"""
Demonstration view.

$Id$
"""


from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile

from loops.browser import common
from loops.browser.concept import ConceptRelationView
from loops.common import adapted
from loops import util


template = ViewPageTemplateFile('view_macros.pt')
conceptMacrosTemplate = common.conceptMacrosTemplate


class GlossaryItemView(common.BaseView):

    @Lazy
    def macro(self):
        return template.macros['glossaryitem']

    @Lazy
    def conceptMacros(self):
        return conceptMacrosTemplate.macros

    @Lazy
    def children(self):
        rels = sorted(self.context.getChildRelations(),
                      key=(lambda x: x.second.title.lower()))
        for r in rels:
            yield ConceptRelationView(r, self.request, contextIsSecond=True)

