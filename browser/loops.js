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

function validate(nodeName, required) {
    // (work in progress) - may be used for onBlur event handler
    var w = dojo.byId(nodeName);
    if (required && w.value == '') {
        w.setAttribute('style','background-color: #ffff00');
        w.focus();
        return false;
    }
}

function destroyWidgets(node) {
    dojo.forEach(dojo.query('[widgetId]', node), function(n) {
        w = dijit.byNode(n);
        if (w != undefined) {
            w.destroyRecursive();
        }
    });
}

function replaceNode(html, nodeName) {
    var newNode = document.createElement('div');
    newNode.innerHTML = html;
    if (nodeName == undefined) {
        nodeName = newNode.firstChild.getAttribute('id');
    }
    if (nodeName != undefined) {
        newNode.id = nodeName;
        var node = dojo.byId(nodeName);
        destroyWidgets(node);
        var parent = node.parentNode;
        parent.replaceChild(newNode, node);
        dojo.parser.parse(newNode);
    } else {
        window.location.href = url;
    }
}

function updateNode(url, nodeName) {
    dojo.xhrGet({
        url: url,
        handleAs: 'text',
        load: function(response, ioArgs) {
            replaceNode(response, nodeName);
        }
    });
}

function replaceFieldsNode(targetId, typeId, url) {
    token = dojo.byId(typeId).value;
    uri = url + '?form.type=' + token;
    updateNode(uri, 'form.fields');
}

function replaceFieldsNodeForLanguage(targetId, langId, url) {
    lang = dojo.byId(langId).value;
    uri = url + '?loops.language=' + lang;
    updateNode(uri, 'form.fields');
}

function submitReplacing(targetId, formId, url) {
    dojo.xhrPost({
        url: url,
        form: dojo.byId(formId),
        mimetype: "text/html",
        load: function(response, ioArgs) {
            replaceNode(response, targetId);
        }
    })
}

function xhrSubmitPopup(formId, url) {
    dojo.xhrPost({
        url: url,
        form: dojo.byId(formId),
        mimetype: "text/html",
        load: function(response, ioArgs) {
            window.close();
        }
    });
}

function setConceptTypeForComboBox(typeId, cbId) {
    var t = dojo.byId(typeId).value;
    var cb = dijit.byId(cbId);
    var dp = cb.store;
    var baseUrl = dp.url.split('?')[0];
    var newUrl = baseUrl + '?searchType=' + t;
    dp.url = newUrl;
    cb.setDisplayedValue('');
}

var dialog;
var dialogName

function objectDialog(dlgName, url) {
    dojo.require('dijit.Dialog');
    dojo.require('dojo.parser');
    dojo.require('dijit.form.FilteringSelect');
    dojo.require('dojox.data.QueryReadStore');
    if (dialogName == undefined || dialogName != dlgName) {
        if (dialog != undefined) {
            dialog.destroyRecursive();
        }
        dialogName = dlgName;
        dialog = new dijit.Dialog({
                    href: url
                        }, dojo.byId('dialog.' + dlgName));
    }
    dialog.show();
}

function addConceptAssignment(prefix, suffix) {
    node = dojo.byId('form.' + suffix);
    widget = dijit.byId(prefix + '.search.text');
    cToken = widget.getValue();
    title = widget.getDisplayedValue();
    if (cToken.length == 0) {
        alert('Please select a concept!');
        return false;
    }
    pToken = dojo.byId(prefix + '.search.predicate').value;
    token = cToken + ':' + pToken;
    var td = document.createElement('td');
    td.colSpan = 5;
    td.innerHTML = '<input type="checkbox" name="form.' + suffix + '.selected:list" value="' + token + '" checked> <span>' + title + '</span>';
    var tr = document.createElement('tr');
    tr.appendChild(td);
    node.appendChild(tr);
}

function closeDataWidget(save) {
    var widget = dijit.byId('data');
    if (widget != undefined && save) {
        value = widget.getValue();
        //widget.close(save);
        form = dojo.byId('dialog_form');
        var ta = document.createElement('textarea');
        ta.name = 'data';
        ta.value = value;
        form.appendChild(ta);
    }
}

var editor;

function inlineEdit(id) {
    if (editor == undefined) {
        editor = new dijit.Editor({}, dojo.byId(id));
    }
}
