/* $Id$ */

function openEditWindow(url) {
    zmi = window.open(url, 'zmi');
    zmi.focus();
    return false;
}

function focusOpener() {
    if (typeof(opener) != 'undefined' && opener != null) {
        opener.location.reload();
        opener.focus();
    }
}

function replaceFieldsNode(targetId, typeId, url) {
    token = dojo.byId(typeId).value;
    uri = url + '?form.type=' + token;
    dojo.io.updateNode(targetId, uri);
}

function replaceFieldsNodeForLanguage(targetId, langId, url) {
    lang = dojo.byId(langId).value;
    uri = url + '?loops.language=' + lang;
    dojo.io.updateNode(targetId, uri);
}

function submitReplacing(targetId, formId, actionUrl) {
    dojo.io.updateNode(targetId, {
            url: actionUrl,
            formNode: dojo.byId(formId),
            method: 'post'
        });
    return false;
}

function xhrSubmitPopup(formId, actionUrl) {
    dojo.io.bind({
        url: actionUrl,
        formNode: dojo.byId(formId),
        method: 'post',
        mimetype: "text/html",
        load: function(t, d, e) {
            window.close();
        }
    });
}

function submitReplacingOrReloading(targetId, formId, actionUrl) {
    node = dojo.byId(targetId);
    var args = {
        url: actionUrl,
        formNode: dojo.byId(formId),
        method: 'post',
        mimetype: "text/html"
    };
    args.load = function (t, d, e) {
        if (d.length < 10) {
            document.location.reload(false);
        } else {
            while (node.firstChild) {
                dojo.dom.destroyNode(node.firstChild);
            }
            node.innerHTML = d;
        }
    };
    dojo.io.bind(args);
    return false;
}

function inlineEdit(id, saveUrl) {
    var iconNode = dojo.byId('inlineedit_icon');
    iconNode.style.visibility = 'hidden';
    editor = dojo.widget.createWidget('Editor',
        {items: ['save', '|', 'formatblock', '|',
                 'insertunorderedlist', 'insertorderedlist', '|',
                 'bold', 'italic', '|', 'createLink', 'insertimage'],
         saveUrl: saveUrl,
         //closeOnSave: true,
         htmlEditing: true
        //onClose: function() {
        /* onSave: function() {
            this.disableToolbar(true);
            iconNode.style.visibility = 'visible';
            //window.location.reload();
         }*/
    }, dojo.byId(id));
    editor._save = function (e) {
            if (!this._richText.isClosed) {
                if (this.saveUrl.length) {
                    var content = {};
                    this._richText.contentFilters = [];
                    content[this.saveArgName] = this.getHtml();
                    content['version'] = 'this';
                    dojo.io.bind({method:this.saveMethod,
                                  url:this.saveUrl,
                                  content:content,
                                  handle:function(type, data, ti, kwargs) {
                                    location.reload(false);
                                  }
                                 }); //alert('save');
                } else {
                    dojo.debug("please set a saveUrl for the editor");
                }
                if (this.closeOnSave) {
                    this._richText.close(e.getName().toLowerCase() == "save");
                }
            }
    }
    return false;
}

function setConceptTypeForComboBox(typeId, cbId) {
    var t = dojo.byId(typeId).value;
    var cb = dojo.widget.manager.getWidgetById(cbId);
    var dp = cb.dataProvider;
    var baseUrl = dp.searchUrl.split('&')[0];
    var newUrl = baseUrl + '&searchType=' + t;
    dp.searchUrl = newUrl;
    cb.setValue('');
}

var dialogs = {}

function objectDialog(dlgName, url) {
    dojo.require('dojo.widget.Dialog');
    dojo.require('dojo.widget.ComboBox');
    dlg = dialogs[dlgName];
    if (!dlg) {
        //dlg = dojo.widget.fromScript('Dialog',
        dlg = dojo.widget.createWidget('Dialog',
            {bgColor: 'white', bgOpacity: 0.5, toggle: 'fade',
             toggleDuration: 250,
             executeScripts: true,
             href: url
            }, dojo.byId('dialog.' + dlgName));
        dialogs[dlgName] = dlg;
    }
    dlg.show();
}

function addConceptAssignment(prefix, suffix) {
    dojo.require('dojo.html')
    node = dojo.byId('form.' + suffix);
    els = document.forms[0].elements;
    for (var i=0; i<els.length; i++) { //getElementsByName does not work here in IE
        el = els[i];
        if (el.name == prefix + '.search.text_selected') {
            cToken = el.value;
        } else if (el.name == prefix + '.search.text') {
            title = el.value;
        }
    }
    if (cToken.length == 0) {
        alert('Please select a concept!');
        return false;
    }
    pToken = dojo.byId(prefix + '.search.predicate').value;
    token = cToken + ':' + pToken;
    var td = document.createElement('td');
    td.colSpan = 5;
    td.innerHTML = '<input type="checkbox" name="form.' + suffix + '.selected:list" value="' + token + '" checked><span>' + title + '</span>';
    var tr = document.createElement('tr');
    tr.appendChild(td);
    node.appendChild(tr);
}

