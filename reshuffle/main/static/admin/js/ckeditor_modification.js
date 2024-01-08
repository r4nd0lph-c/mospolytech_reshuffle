// on page load actions
window.addEventListener("load", () => {
    const state = window.location.pathname.split("/").at(-2);
    if (state === "add" || state === "change") {
        // move CKEditor window to separate line
        let editor = document.getElementsByClassName("django-ckeditor-widget")[0];
        let container = editor.parentElement;
        container.classList = null;
        // remove "advanced" settings and unused fields in table dialog
        CKEDITOR.on("dialogDefinition", function (ev) {
            if (ev.data.name === "table" || ev.data.name === "tableProperties") {
                let dialog_definition = ev.data.definition;
                dialog_definition.removeContents("advanced");
                let info_tab = dialog_definition.getContents("info");
                info_tab.remove("txtSummary");
            }
        });
    }
});