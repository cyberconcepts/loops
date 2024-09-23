#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
Elements for handling and presentation of pseudo folders.
"""


from cybertools.browser.action import actions
from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.util import _


actions.register('createFolder', 'portlet', DialogAction,
        title=_(u'Create Folder...'),
        description=_(u'Create a new folder.'),
        viewName='create_concept.html',
        dialogName='createFolder',
        typeToken='.loops/concepts/folder',
        fixedType=True,
        innerForm='inner_concept_form.html',
)

actions.register('editFolder', 'portlet', DialogAction,
        title=_(u'Edit Folder...'),
        description=_(u'Modify folder.'),
        viewName='edit_concept.html',
        dialogName='editFolder',
)


class FolderView(ConceptView):

    def getActions(self, category='concept', page=None, target=None):
        # obsolete: define actions via type option
        if category == 'portlet':
            return actions.get(category, ['createFolder', 'editFolder'],
                               view=self, page=page, target=target)
        return []

