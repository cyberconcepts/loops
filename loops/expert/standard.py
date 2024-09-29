# loops.expert.standard

""" loops standard reports.
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
        print('***', self.targets, result)
        return result

