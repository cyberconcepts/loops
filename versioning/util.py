#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Utilities for managing version informations.

$Id$
"""

from loops.versioning.interfaces import IVersionable


def getVersion(obj, request):
    """ Check if another version should be used for the object
        provided and return it.
    """
    versionRequest = request.form.get('version')
    if versionRequest == 'this':
        # we really want this object, not another version
        return obj
    versionable = IVersionable(obj, None)
    if versionable is None:
        return obj
    if versionRequest:
        # we might have a versionId in the request
        v = versionable.versions.get(versionRequest)
        if v is not None:
            return v
    # find and return a standard version
    v = versionable.releasedVersion
    if v is None:
        v = versionable.currentVersion
    return v


def getMaster(obj):
    versionable = IVersionable(obj, None)
    if versionable is None:
        return obj
    return versionable.master

