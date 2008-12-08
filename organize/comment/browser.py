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
Definition of view classes and other browser related stuff for comments.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import actions
from loops.browser.action import DialogAction
from loops.browser.common import BaseView
from loops.util import _


comment_macros = ViewPageTemplateFile('comment_macros.pt')

actions.register('addComment', 'button', DialogAction,
        title=_(u'Add Comment'),
        description=_(u'Add a comment to this object.'),
        viewName='create_comment.html',
        dialogName='createComment',
        innerForm='inner_comment_form.html',
        #prerequisites=['registerDojoDateWidget'],
)


class CommentsView(BaseView):

    pass

