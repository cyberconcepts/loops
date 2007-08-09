#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
Definition of view classes for the top-level loops container.

$Id$
"""

from zope.app import zapi
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.event import notify
from zope.formlib.form import FormFields
from loops.base import Loops
from loops.interfaces import ILoops
from loops.browser.common import AddForm, EditForm, BaseView
from loops.setup import ISetupManager
from loops.util import _


class LoopsAddForm(AddForm):

    form_fields = AddForm.form_fields + FormFields(ILoops)
    label = _(u'Create Loops Site')

    def createAndAdd(self, data):
        container = self.context.context
        name = data.pop('name', 'loopsdemo')
        loops = Loops()
        self.context.contentName = name
        for attr in data:
            setattr(loops, attr, data[attr])
        notify(ObjectCreatedEvent(loops))
        self.context.add(loops)
        setup = ISetupManager(loops, None)
        if setup is not None:
            setup.setup()
        return loops


class LoopsEditForm(EditForm):

    form_fields = FormFields(ILoops)


