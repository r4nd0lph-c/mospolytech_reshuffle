window.addEventListener("load", () => {
    const state = window.location.pathname.split("/").at(-2);
    if (state === "add" || state === "change") {
        console.log("model 'part' validation");
    }
});