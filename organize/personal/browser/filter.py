#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
A view (to be used by listings, portlets, ...) for filters.

$Id$
"""

from zope import component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.configurator import ViewConfigurator, MacroViewProperty
from cybertools.stateful.interfaces import IStateful
from loops.browser.node import NodeView
from loops.concept import Concept
from loops.organize.party import getPersonForUser
from loops.organize.personal.interfaces import IFilters
from loops import util


personal_macros = ViewPageTemplateFile('personal_macros.pt')


class FilterView(NodeView):

    @Lazy
    def item(self):
        return self

    @Lazy
    def person(self):
        return getPersonForUser(self.context, self.request)

    @Lazy
    def targetUid(self):
        target = self.virtualTargetObject
        if (target and isinstance(target, Concept) and
                target.conceptType != self.conceptManager.getTypeConcept()):
            return util.getUidForObject(target)
        else:
            return None


    @Lazy
    def filters(self):
        records = self.loopsRoot.getRecordManager()
        if records is not None:
            storage = records.get('filters')
            if storage is not None:
                return IFilters(storage)
        return None

    def listFilters(self):
        if self.filters is None:
            return
        for uid in self.filters.list(self.person):
            obj = util.getObjectForUid(uid)
            if obj is not None:
                yield dict(url=self.getUrlForTarget(obj),
                           uid=uid,
                           title=obj.title,
                           typeTitle=obj.getType().title,
                           description=obj.description,
                           object=obj)

    def add(self):
        if self.filters is None:
            return
        uid = self.request.get('id')
        if not uid:
            return
        obj = util.getObjectForUid(uid)
        self.filters.add(obj, self.person)
        self.request.response.redirect(self.virtualTargetUrl)

    def deactivate(self):
        if self.filters is None:
            return
        id = self.request.get('id')
        if not id:
            return
        #self.filters.deactivate(id)
        self.filters.remove(id, self.person)
        self.request.response.redirect(self.virtualTargetUrl)

    @Lazy
    def filterStructure(self):
        result = {}
        for item in self.listFilters():
            obj = item['object']
            result.setdefault(obj.getType(), set([])).add(obj)
        return result

    def checkOptions(self, obj, options):
        if isinstance(options, list):
            return True
        form = self.request.form
        if form.get('filter.states') == 'all':
            return True
        filterStates = options
        for std in filterStates.keys():
            formStates = form.get('filter.states.' + std)
            if formStates == 'all':
                continue
            stf = component.getAdapter(obj, IStateful, name=std)
            if formStates:
                if stf.state not in formStates.split(','):
                    return False
            else:
                if stf.state not in getattr(filterStates, std):
                    return False
        return True

    def check(self, obj, options=None):
        if options is not None: 
            if not self.checkOptions(obj, options):
                return False
        fs = self.filterStructure
        if not fs:
            return True
        for objs in fs.values():
            if obj in objs:     # the filtered object itself is always shown
                return True
        checked = {}
        parents = [pi.object for pi in obj.getAllParents(ignoreTypes=True)]
        if isinstance(obj, Concept):
            parents.insert(0, obj)
        for p in parents:
            for t, v in fs.items():
                if checked.get(t):  # type already present and set to True
                    continue
                if p.conceptType == t:  # type has to be checked
                    checked[t] = (p in v)
        for x in checked.values():
            if not x:
                return False
        return True

    def apply(self, seq):
        return [obj for obj in seq if self.check(obj)]

