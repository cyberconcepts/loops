/* $Id$ */

function openEditWindow(url) {
    zmi=window.open(url, 'zmi');
    zmi.focus();
    return false;
}
function focusOpener() {
    if (typeof(opener) != 'undefined' && opener != null) {
        opener.location.reload();
        opener.focus();
    }
}
