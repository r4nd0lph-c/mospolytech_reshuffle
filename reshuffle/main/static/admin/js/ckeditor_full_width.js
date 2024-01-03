window.onload = () => {
    const state = window.location.pathname.split("/").at(-2);
    if (state === "add" || state === "change") {
        let textarea = document.getElementById("id_content");
        let container = textarea.parentElement.parentElement;
        container.classList = null;
    }
};