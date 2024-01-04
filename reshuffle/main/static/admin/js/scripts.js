window.addEventListener("load", () => {
    const state = window.location.pathname.split("/").at(-2);

    // Adapts the sizes of images and tables in the main table
    if (state === "docheader") {
        const MAX_CONTENT_WIDTH = 500;
        let table = document.getElementById("result_list");
        let rows = table.children[1].children;
        for (let row of rows) {
            let container = row.children[2].firstChild;
            for (let e of container.getElementsByTagName("img")) {
                e.removeAttribute("height");
                e.setAttribute("width", `${MAX_CONTENT_WIDTH}px`);
                e.setAttribute("style", "border: 1px solid var(--hairline-color)");
            }
            for (let e of container.getElementsByTagName("table")) {
                e.removeAttribute("style");
            }
        }
    }
});