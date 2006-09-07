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

function listConceptsForComboBox() {
    return [['Zope', 'zope'], ]
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
    var iconNode = dojo.byId("inlineedit_icon");
    iconNode.style.visibility = "hidden";
    var editor = dojo.widget.fromScript("Editor",
        {items: ["save", "|", "formatblock", "|",
                 "insertunorderedlist", "insertorderedlist", "|",
                 "bold", "italic", "|", "createLink", "insertimage"],
         saveUrl: saveUrl,
         closeOnSave: true,
         onSave: function(){
            this.disableToolbar(true);
            iconNode.style.visibility = "visible";}
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

