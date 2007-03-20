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
Versioning interfaces.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema


class IVersionable(Interface):
    """ An object that may exist in different versions.
    """

    versionNumbers = Attribute(u'A tuple of version numbers for the context '
                        'object, with a number for each level')

    variantIds = Attribute(u'A tuple of variant IDs (e.g. for language '
                        'varuants) for the context object')

    versionId = Attribute(u'A string identifying this version, e.g. 1.1_de, '
                        'derived from versionNumbers and variantIds')

    master = Attribute(u'The object (master version) that should be used for access to '
                        'version-independent attributes and central '
                        'versioning metadata')

    # attributes taken from the master version:

    versions = Attribute(u'A dictionary of all versions of this object')

    currentVersion = Attribute(u'The default version to be used for editing')

    releasedVersion = Attribute(u'The default version to be used for viewing')

    def createVersion(level=1):
        """ Create a copy of the context object as a new version and return it.

            The level of the version says if it is a minor (1) or major (0)
            version. (It would even be possible to have more than two levels.
        """

    def createVariant(id, level=0):
        """ Create a copy of the context object as a new variant and return it.

            The level provides the position in the variantIds tuple.
        """

