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
Common stuff.

$Id$
"""

from zope import component
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from zope.security.proxy import removeSecurityProxy
from persistent.mapping import PersistentMapping

from cybertools.typology.interfaces import IType
from loops.common import adapted, AdapterBase


_not_found = object()

# support for i18n content

class I18NValue(PersistentMapping):
    """ A dictionary to be used for storing values for different languages.
    """

    default = None

    def lower(self):
        # this should only be used as a fallback for the title attribute
        return self.getDefault().lower()

    def getDefault(self):
        if self.default is None:
            return self.values()[0]
        return self.default

    def __str__(self):
        return str(self.getDefault())

    #def __unicode__(self):
    #    return unicode(self.getDefault())

    #def __repr__(self):
    #    return repr(self.getDefault())


def getI18nValue(obj, attr, langInfo=None):
    obj = removeSecurityProxy(obj)
    value = getattr(obj, attr, None)
    if isinstance(value, I18NValue):
        if langInfo:
            result = value.get(langInfo.language, _not_found)
            if result is _not_found:
                result = value.get(langInfo.defaultLanguage, _not_found)
                if result is _not_found:
                    result = value.getDefault()
            return result
        else:
            return value.getDefault()
    return value

def setI18nValue(obj, attr, value, langInfo=None):
    obj = removeSecurityProxy(obj)
    old = getattr(obj, attr, None)
    if langInfo is None:
        if isinstance(old, I18NValue):
            raise ValueError('Attribute %s on object %s is an I18NValue (%s) '
                             'and no langInfo given.' % (attr, obj, value))
        else:
            setattr(obj, attr, value)
            return
    lang = langInfo.language
    if isinstance(old, I18NValue):
        old[lang] = value
    else:
        i18nValue = I18NValue(((lang, value),))
        defaultLang = langInfo.defaultLanguage
        if lang != defaultLang:
            # keep existing value
            i18nValue[defaultLang] = old
        i18nValue.default = i18nValue[defaultLang]
        setattr(obj, attr, i18nValue)
    #print '*** setI18nValue', attr, langInfo, lang, value, getattr(obj, attr, None)


class I18NAdapterBase(AdapterBase):
    """ Base (or mix-in) class for concept adapters for internationalization of
        context attributes.
    """

    _adapterAttributes = AdapterBase._adapterAttributes + ('languageInfo',)
    languageInfo = None

    @Lazy
    def i18nAttributes(self):
        tp = IType(self.context)
        attrs = tp.optionsDict.get('i18nattributes', '')
        return [attr.strip() for attr in attrs.split(',')]

    def __getattr__(self, attr):
        self.checkAttr(attr)
        langInfo = attr in self.i18nAttributes and self.languageInfo or None
        return getI18nValue(self.context, '_' + attr, langInfo)

    def __setattr__(self, attr, value):
        if attr in self._adapterAttributes:
            object.__setattr__(self, attr, value)
        else:
            langInfo = attr in self.i18nAttributes and self.languageInfo or None
            self.checkAttr(attr)
            setI18nValue(self.context, '_' + attr, value, langInfo)

    def translations(self, attr='title', omitCurrent=True):
        langInfo = self.languageInfo
        if langInfo:
            langs = langInfo.availableLanguages
            if len(langs) > 1:
                value = getattr(removeSecurityProxy(self.context), '_' + attr, None)
                if isinstance(value, I18NValue):
                    result = dict((k, v) for k, v in value.items() if v)
                    if omitCurrent and langInfo.language in result:
                        del result[langInfo.language]
                    return result
        return {}
