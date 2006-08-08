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
