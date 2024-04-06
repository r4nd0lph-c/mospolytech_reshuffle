// on page load actions
window.addEventListener("load", () => {
    // load jQuery
    if (typeof (django) !== "undefined" && typeof (django.jQuery) !== "undefined") {
        (function ($) {
            const state = window.location.pathname.split("/").at(-2);
            if (state === "change") {
                // find alias
                let alias_container = document.getElementsByClassName("field-alias")[0].children[0].children[0].children[1];
                let alias = alias_container.textContent;

                // send request to backend, receive image url by its alias
                function get_scan_url() {
                    $.ajax({
                        type: "GET",
                        url: URL_MODIFICATION_VERIFIED_WORK_ENTRY,
                        data: {
                            csrfmiddlewaretoken: CSRF_TOKEN,
                            alias: alias
                        },
                        success: function (data) {
                            show_image(data);
                        },
                        error: function () {
                            console.log("get_scan_url() error");
                        }
                    });
                }

                // show received image
                function show_image(data) {
                    let url = data["url"];
                    alias_container.innerHTML = "";
                    if (url) {
                        let img = document.createElement("img");
                        img.src = url;
                        img.style.width = "100%";
                        img.style.height = "auto";
                        alias_container.appendChild(img);
                    } else {
                        alias_container.innerHTML = data["error"];
                    }
                }

                // activation
                get_scan_url();
            }
        }(django.jQuery));
    }
});