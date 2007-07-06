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
Utilities for the loops.organize package.

$Id$
"""

from zope import interface, component, schema
from zope.app.authentication.interfaces import IPluggableAuthentication
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.security.interfaces import IAuthentication

authPluginId = 'loops'


def getPrincipalFolder(context=None):
    pau = component.getUtility(IAuthentication, context=context)
    if not IPluggableAuthentication.providedBy(pau):
        raise ValueError(u'There is no pluggable authentication '
                          'utility available.')
    if not authPluginId in pau.authenticatorPlugins:
        raise ValueError(u'There is no loops authenticator '
                          'plugin available.')
    for name, plugin in pau.getAuthenticatorPlugins():
        if name == authPluginId:
            return plugin


def getInternalPrincipal(id, context=None):
    pau = component.getUtility(IAuthentication, context=context)
    if not IPluggableAuthentication.providedBy(pau):
        raise ValueError(u'There is no pluggable authentication '
                          'utility available.')
    if not id.startswith(pau.prefix):
        next = queryNextUtility(pau, IAuthentication)
        if next is None:
            raise PrincipalLookupError(id)
        return next.getPrincipal(id)
    id = id[len(pau.prefix):]
    for name, authplugin in pau.getAuthenticatorPlugins():
        if not id.startswith(authplugin.prefix):
            continue
        principal = authplugin.get(id[len(authplugin.prefix):])
        if principal is None:
            continue
        return principal
    next = queryNextUtility(pau, IAuthentication)
    if next is not None:
        return next.getPrincipal(pau.prefix + id)
    raise PrincipalLookupError(id)
