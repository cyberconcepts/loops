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
    dojo.io.updateNode(targetId, {
            url: url + '?form.type=' + token
    });
}

function submitReplacing(targetId, formId, actionUrl) {
    dojo.io.updateNode(targetId, {
            url: actionUrl,
            formNode: dojo.byId(formId),
            method: 'post'
        });
    return false;
}

function inlineEdit(id, saveUrl) {
    //dojo.require('dojo.widget.Editor');
    var iconNode = dojo.byId('inlineedit_icon');
    iconNode.style.visibility = 'hidden';
    //var editor = dojo.widget.fromScript('Editor',
    editor = dojo.widget.createWidget('Editor',
        {items: ['save', '|', 'formatblock', '|',
                 'insertunorderedlist', 'insertorderedlist', '|',
                 'bold', 'italic', '|', 'createLink', 'insertimage'],
         saveUrl: saveUrl,
         closeOnSave: true,
         htmlEditing: true,
         //onClose: function() {
         onSave: function() {
            this.disableToolbar(true);
            iconNode.style.visibility = 'visible';
            //window.location.reload();
            }
        }, dojo.byId(id));
    return false;
}

function setConceptTypeForComboBox(typeId, cbId) {
    var t = dojo.byId(typeId).value;
    var dp = dojo.widget.manager.getWidgetById(cbId).dataProvider;
    var baseUrl = dp.searchUrl.split('&')[0];
    var newUrl = baseUrl + '&searchType=' + t;
    dp.searchUrl = newUrl;
}

var dialogs = {}

function objectDialog(dlgName, url) {
    dojo.require('dojo.widget.Dialog');
    dojo.require('dojo.widget.ComboBox');
    dlg = dialogs[dlgName];
    if (!dlg) {
        //dlg = dojo.widget.fromScript('Dialog',
        dlg = dojo.widget.createWidget('Dialog',
            {bgColor: 'white', bgOpacity: 0.5, toggle: 'fade', toggleDuration: 250,
             executeScripts: true,
             href: url
            }, dojo.byId('dialog.' + dlgName));
        dialogs[dlgName] = dlg;
    }
    dlg.show();
}

function addConceptAssignment() {
    node = dojo.byId('form.assignments');
    cToken = document.getElementsByName('concept.search.text_selected')[0].value;
    if (cToken.length == 0) {
        alert('Please select a concept!');
        return false;
    }
    pToken = dojo.byId('concept.search.predicate').value;
    token = cToken + ':' + pToken;
    title = document.getElementsByName('concept.search.text')[0].value;
    var td = document.createElement('td');
    td.setAttribute('colspan', '5');
    td.innerHTML = '<input type="checkbox" name="form.assignments.selected:list" value="' + token + '" checked><span>' + title + '</span>';
    var tr = document.createElement('tr');
    tr.appendChild(td);
    node.appendChild(tr);
}

