window.onload = () => {
    const state = window.location.pathname.split("/").at(-2);
    if (state === "add" || state === "change") {

        // Moves CKEditor window to a separate line
        let textarea = document.getElementById("id_content");
        let container = textarea.parentElement.parentElement;
        container.classList = null;

        // Removes "advanced" settings and unused fields for table dialog
        CKEDITOR.on("dialogDefinition", function (ev) {
            if (ev.data.name === "table" || ev.data.name === "tableProperties") {
                let dialog_definition = ev.data.definition;
                dialog_definition.removeContents("advanced");
                let info_tab = dialog_definition.getContents("info");
                info_tab.remove("txtSummary");
            }
        });
    }
};