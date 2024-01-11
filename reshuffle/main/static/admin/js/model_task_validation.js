// load jQuery
if (!$) {
    $ = django.jQuery;
}

// wrap other functions, reduces workload
function debounce(func, timeout = 100) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            func.apply(this, args);
        }, timeout);
    };
}

// on page load actions
window.addEventListener("load", () => {
    const state = window.location.pathname.split("/").at(-2);
    if (state === "add" || state === "change") {
        // find part & position with label
        let part = document.getElementById("id_part");
        let position = document.getElementById("id_position");
        let label = document.getElementById("id_position_helptext").children[0];

        // send request to backend, receive validation info
        function validation_task(id_prt) {
            $.ajax({
                type: "GET",
                url: URL_VALIDATION_TASK,
                data: {
                    csrfmiddlewaretoken: CSRF_TOKEN,
                    id_prt: id_prt
                },
                success: function (data) {
                    validate(id_prt, data);
                },
                error: function () {
                    console.log("validation_task() error");
                }
            });
        }

        // validate position with label based on received data
        function validate(id_prt, data) {
            // enable / disable position & change label
            if (id_prt) {
                let old_selected_val = position.value === "" ? data["amount_min"] : position.value;
                position.disabled = false;
                position.min = data["amount_min"];
                position.max = data["amount_max"];
                if (old_selected_val > data["amount_max"])
                    position.value = data["amount_max"];
                else if (old_selected_val < data["amount_min"])
                    position.value = data["amount_min"];
                else
                    position.value = old_selected_val;
                label.innerHTML = `${data["labels"][1]}: [${data["amount_min"]} – ${data["amount_max"]}]`;
            } else {
                position.disabled = true;
                position.value = "";
                label.innerHTML = data["labels"][0];
            }
            // handler for position
            position.onchange = () => {
                position.value = Math.min(position.value, data["amount_max"]);
                position.value = Math.max(position.value, data["amount_min"]);
            }
        }

        // add onchange listener for part
        let debounced_validation_task = debounce(validation_task);
        part.onchange = () => {
            debounced_validation_task(part.value);
        }

        // check initialized part value
        validation_task(part.value);
    }
});