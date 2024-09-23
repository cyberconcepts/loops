#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
Blogs (weblogs) and blog posts.
"""

from datetime import datetime
from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.compound.interfaces import ICompound
from loops.interfaces import HtmlText
from loops.util import _


class ISimpleBlogPost(ICompound):
    """ An item on a blog, sort of a diary item, minimal version.
    """

    date = schema.Datetime(
                title=_(u'Date/Time'),
                description=_(u'The date and time the information '
                        'was posted.'),
                required=True,)
    date.default_method = datetime.now
    creator = schema.ASCIILine(
                title=_(u'Creator'),
                description=_(u'The principal id of the user that created '
                        'the blog post.'),
                readonly=True,
                required=False,)
    text = HtmlText(
                title=_(u'Text'),
                description=_(u'The text of your blog entry'),
                required=False)


class IBlogPost(ICompound):
    """ An item on a blog, sort of a diary item.
    """

    date = schema.Datetime(
                title=_(u'Date/Time'),
                description=_(u'The date and time the information '
                        'was posted.'),
                required=True,)
    date.default_method = datetime.now
    private = schema.Bool(
                title=_(u'Private'),
                description=_(u'Check this field if the blog post '
                        'should be accessible only for a limited audience.'),
                required=False)
    creator = schema.ASCIILine(
                title=_(u'Creator'),
                description=_(u'The principal id of the user that created '
                        'the blog post.'),
                readonly=True,
                required=False,)
    text = schema.Text(
                title=_(u'Text'),
                description=_(u'The text of your blog entry'),
                required=False)
    privateComment = schema.Text(
                title=_(u'Private Comment'),
                description=_(u'A text that is not visible for other users.'),
                required=False)

