#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Definition of view classes and other browser related stuff (e.g. actions) for
loops.organize.party.

$Id$
"""

from zope import interface, component
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import actions
from loops.browser.action import DialogAction
from loops.util import _


actions.register('createPerson', 'portlet', DialogAction,
        title=_(u'Create Person...'),
        description=_(u'Create a new person.'),
        viewName='create_concept.html',
        dialogName='createPerson',
        typeToken='.loops/concepts/person',
        fixedType=True,
        innerForm='inner_concept_form.html',
        prerequisites=['registerDojoDateWidget'],
)

actions.register('editPerson', 'portlet', DialogAction,
        title=_(u'Edit Person...'),
        description=_(u'Modify person.'),
        viewName='edit_concept.html',
        dialogName='editPerson',
        prerequisites=['registerDojoDateWidget'],
)

actions.register('createAddress', 'portlet', DialogAction,
        title=_(u'Create Address...'),
        description=_(u'Create a new address.'),
        viewName='create_concept.html',
        dialogName='createAddress',
        typeToken='.loops/concepts/address',
        fixedType=True,
        innerForm='inner_concept_form.html',
)

actions.register('editAddress', 'portlet', DialogAction,
        title=_(u'Edit Address...'),
        description=_(u'Modify address.'),
        viewName='edit_concept.html',
        dialogName='editAddress',
)
