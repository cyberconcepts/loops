/* loops.js */

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

function toggleCheckBoxes(toggle, fieldName) {
    var w = toggle.form[fieldName];
    if (w[0] == null) w = [w];
    for (i in w) w[i].checked=toggle.checked;
}

function setRadioButtons(value) {
    dojo.forEach(dojo.query('input[type="radio"][value="' + value + '"]'), 
                        function(n) {
                            n.checked = true;})
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

function showIf(node, value, targetName) {
    var display = (node.value == value) ? 'inline' : 'none';
    dojo.byId(targetName).style.display = display;
}

function showIfIn(node, conditions) {
    dojo.forEach(conditions, function(cond) {
        var display = (node.value == cond[0]) ? '' : 'none';
        dojo.byId(cond[1]).style.display = display;
    })
}

function setIfIn(node, conditions) {
    dojo.forEach(conditions, function(cond) {
        if (node.value == cond[0]) {
            target = dijit.byId(cond[1]);
            target.setValue(cond[2]);
        }
    })
}

function setIf(node, cond, acts) {
    if (node.value == cond) {
        dojo.forEach(acts, function(act) {
            target = dijit.byId(act[0]);
            target.setValue(act[1]);
        })
    }
}

function setIfN(node, conds, acts) {
    dojo.forEach(conds, function(cond) {
        if (node.value == cond) {
            dojo.forEach(acts, function(act) {
                target = dijit.byId(act[0]);
                target.setValue(act[1]);
            })
        }
    })
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
            return response;
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
            return response;
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

function objectDialog(dlgName, url) {
    dojo.require('dijit.Dialog');
    dojo.require('dojo.parser');
    dojo.require('dijit.form.FilteringSelect');
    dojo.require('dojox.data.QueryReadStore');
    if (dialog != undefined) {
        dialog.destroyRecursive();
    }
    dialog = new dijit.Dialog({
                href: url
                    }, dojo.byId('dialog.' + dlgName));
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

function addRelation(fieldName) {
    valuesNode = dojo.byId(fieldName + '_values');
    widget = dijit.byId(fieldName + '_search');
    token = widget.getValue();
    if (token) {
        title = widget.getDisplayedValue();
        ih = '<div><input type="checkbox" name="' + fieldName + ':list" value="' + token + '" checked> <span>' + title + '</span></div>';
        newNode = document.createElement('div');
        newNode.innerHTML = ih;
        valuesNode.appendChild(newNode);
    }
}

function setRelation(fieldName) {
    valuesNode = dojo.byId(fieldName + '_values');
    widget = dijit.byId(fieldName + '_search');
    token = widget.getValue();
    if (token) {
        title = widget.getDisplayedValue();
        ih = '<div><input type="checkbox" name="' + fieldName + '" value="' + token + '" checked> <span>' + title + '</span></div>';
        newNode = document.createElement('div');
        newNode.innerHTML = ih;
        valuesNode.replaceChild(newNode, valuesNode.firstChild);
    }
}

function validate() {
    //var form = dijit.byId('dialog_form');
    var form = dojo.byId('dialog_form');
    /*if (form != undefined && !form.isValid()) {
        return false;
    }*/
    var titleField = dojo.byId('title');
    if (titleField != undefined && titleField.value == '') {
        return false;
    }
    if (form != undefined) {
        return form.submit();
    }
    return true;
}

function closeDialog(save) {
    closeDataWidget(save);
    if (save && !validate()) {
        return false;
    }
    dialog.hide();
    return true;
}

function closeDataWidget(save) {
    form = dojo.byId('dialog_form');
    dojo.query('.dijitEditor').forEach(function(item, index) {
        console.log(item);
        var name = item.id;
        var widget = dijit.byId(name);
        value = widget.getValue();
        var ta = document.createElement('input');
        ta.type = 'hidden';
        ta.name = name;
        ta.value = value;
        form.appendChild(ta);
    });
}


function xx_closeDataWidget(save) {
    var widget = dijit.byId('data');
    if (widget != undefined && save) {
        value = widget.getValue();
        //widget.close(save);
        form = dojo.byId('dialog_form');
        var ta = document.createElement('input');
        ta.type = 'hidden';
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

// FCKeditor stuff

function createFCKEditorInstance(fieldName, width, height) {
    var editor = new FCKeditor(fieldName);
    /*if (document.all) {
        editor.Config['ToolbarStartExpanded'] = false;
    }*/
    editor.BasePath = '/@@/fckeditor/';
    //editor.Config['SkinPath'] = editor.BasePath + 'editor/skins/office2003/';
    editor.Config['SkinPath'] = editor.BasePath + 'editor/skins/silver/';
    editor.ToolbarSet = 'Standard';
    editor.Width = width;
    editor.Height = height;
    editor.ReplaceTextarea();
}
