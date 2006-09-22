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
Classes for form presentation and processing.

$Id$
"""

from zope import component, interface, schema
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.formlib.form import Form, FormFields
from cybertools.ajax import innerHtml
from cybertools.browser.controller import FormController
from loops.browser.node import NodeView

class CreateObjectForm(NodeView, Form):

    template = ViewPageTemplateFile('form_macros.pt')

    @property
    def macro(self): return self.template.macros['create']

    form_fields = FormFields(
        schema.TextLine(__name__='title', title=_(u'Title')),
        schema.Text(__name__='body', title=_(u'Body Text')),
        schema.TextLine(__name__='linkUrl', title=_(u'Link'), required=False),
    )

    title = _(u'Enter Note')
    form_action = 'create_resource'

    def __init__(self, context, request):
        super(CreateObjectForm, self).__init__(context, request)
        self.setUpWidgets()
        self.widgets['body'].height = 3

    def __call__(self):
        return innerHtml(self)


class CreateObject(FormController):

    def update(self):
        prefix = 'form.'
        form = self.request.form
        print 'updating...'
        # determine name
        # create object, assign basic concepts (type, ...)
        for k in form.keys():
            if k.startswith(prefix):
                fn = k[len(prefix):]
                value = form[k]
                if fn.startswith('concept.search.'):
                    self.assignConcepts(fn, value)
                else:
                    pass
                    #setattr(obj, fn, value)
                print fn, value

    def assignConcepts(self, fieldName, value):
        pass
