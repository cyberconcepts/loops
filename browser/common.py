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
Common base class for loops browser view classes.

$Id$
"""

from zope.app import zapi
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.app.form.browser.interfaces import ITerms
from zope.app.intid.interfaces import IIntIds
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.interface import implements
from zope.app.publisher.browser import applySkin
from zope.publisher.interfaces.browser import ISkin
from zope.schema.vocabulary import SimpleTerm
from zope.security.proxy import removeSecurityProxy

from cybertools.typology.interfaces import IType
from loops import util

class BaseView(object):

    def __init__(self, context, request):
        #self.context = context
        # TODO: get rid of removeSecurityProxy() call
        self.context = removeSecurityProxy(context)
        self.request = request
        skin = None
        # TODO: get ISkinController adapter instead
        skinName = self.loopsRoot.skinName
        if skinName:
            skin = zapi.queryUtility(ISkin, skinName)
            if skin is not None:
                applySkin(self.request, skin)
        self.skin = skin

    @Lazy
    def resourceBase(self):
        skinSetter = self.skin and ('/++skin++' + self.skin.__name__) or ''
        # TODO: put '/@@' etc after path to site instead of directly after URL0
        return self.request.URL[0] + skinSetter + '/@@'

    @Lazy
    def modified(self):
        """ get date/time of last modification
        """
        dc = ICMFDublinCore(self.context)
        d = dc.modified or dc.created
        return d and d.strftime('%Y-%m-%d %H:%M') or ''

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()
    
    @Lazy
    def url(self):
        return zapi.absoluteURL(self.context, self.request)

    @Lazy
    def token(self):
        return self.loopsRoot.getLoopsUri(self.context)

    @Lazy
    def title(self):
        return self.context.title or zapi.getName(self.context)

    @Lazy
    def value(self):
        return self.context

    @Lazy
    def typeTitle(self):
        type = IType(self.context)
        return type is not None and type.title or None

    @Lazy
    def typeUrl(self):
        type = IType(self.context)
        if type is not None:
            provider = type.typeProvider
            if provider is not None:
                return zapi.absoluteURL(provider, self.request)
        return None

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            yield BaseView(o, request)

    @Lazy
    def uniqueId(self):
        return zapi.getUtility(IIntIds).getId(self.context)


class LoopsTerms(object):
    """ Provide the ITerms interface, e.g. for usage in selection
        lists.
    """

    implements(ITerms)

    def __init__(self, source, request):
        # the source parameter is a view or adapter of a real context object:
        self.source = source
        self.context = source.context
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()
    
    def getTerm(self, value):
        return BaseView(value, self.request)

    def getValue(self, token):
        return self.loopsRoot.loopsTraverse(token)


class InterfaceTerms(object):
    """ Provide the ITerms interface for source list of interfaces.
    """

    implements(ITerms)

    def __init__(self, source, request):
        self.source = source
        self.request = request

    def getTerm(self, value):
        token = '.'.join((value.__module__, value.__name__))
        return SimpleTerm(value, token, token)

    def getValue(self, token):
        return resolve(token)


