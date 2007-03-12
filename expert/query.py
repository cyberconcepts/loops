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
Generic query functionality for retrieving stuff from a loops database

$Id$
"""

from zope import interface, component
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy

from hurry.query.query import Text as BaseText
from hurry.query.query import Eq, Between


titleIndex = ('', 'loops_title')
textIndex = ('', 'loops_text')
typeIndex = ('', 'loops_type')


def Title(value):
    return BaseText(titleIndex, value)

def Text(value):
    return BaseText(textIndex, value)

def Type(value):
    if value.endswith('*'):
        v1 = value[:-1]
        v2 = value[:-1] + '\x7f'
        return Between(typeIndex, v1, v2)
    return Eq(typeIndex, value)

