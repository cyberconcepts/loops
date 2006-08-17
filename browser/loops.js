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

function submitReplacing(targetId, formId, actionUrl) {
    dojo.io.updateNode(targetId, {
            url: actionUrl,
            formNode: dojo.byId(formId),
            method: 'post'
        });
    return false;
}

function inlineEdit(id, saveUrl) {
    var editor = dojo.widget.fromScript("Editor",
        {items: ["save", "|", "formatblock", "|",
                 "insertunorderedlist", "insertorderedlist", "|",
                 "bold", "italic", "|", "createLink", "insertimage"],
         saveUrl: saveUrl,
         closeOnSave: true,
         onSave: function(){this.disableToolbar(true);},
        }, dojo.byId(id));
    return false;
}
