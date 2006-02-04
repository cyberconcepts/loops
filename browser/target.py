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
Class(es) for representing a target attribute, to be used e.g. for
vocabularies and widgets.

$Id$
"""

from zope.app import zapi
from zope.app.form.browser.interfaces import ITerms
from zope.schema.vocabulary import SimpleTerm
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.security.proxy import removeSecurityProxy


class TargetTerms(object):

    implements(ITerms)

    def __init__(self, context, request):
        self.context = context.context # the context parameter is the source object
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    def getTerm(self, value):
        token = self.loopsRoot.getLoopsUri(value)
        return SimpleTerm(value, token, value.title)

    def getValue(self, token):
        return self.loopsRoot.loopsTraverse(token)

