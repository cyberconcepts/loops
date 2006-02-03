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
from zope.schema.interfaces import IIterableSource
from zope.cachedescriptors.property import Lazy
from zope.interface import implements
from zope.security.proxy import removeSecurityProxy


class Term(object):
  
    def __init__(self, **kw):
        self.__dict__.update(kw)


class TargetTerms(object):

    implements(ITerms)

    def __init__(self, context, request):
        self.context = context.context
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    def getTerm(self, value):
        token = self.loopsRoot.getLoopsUri(value)
        #token = value.getLoopsRoot().getLoopsUri(value)
        title = value.title
        return Term(title=title, token=token)

    def getValue(self, token):
        return self.loopsRoot.loopsTraverse(token)


class TargetSourceList(object):

    implements(IIterableSource)

    def __init__(self, context):
        self.context = removeSecurityProxy(context)
        self.resources = self.context.getLoopsRoot()['resources']

    def __iter__(self):
        return iter(self.resources.values())

    def __len__():
        return len(self.resources)


