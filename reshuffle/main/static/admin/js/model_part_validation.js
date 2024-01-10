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
        // find ID of current part
        const id_prt = state === "change" ? window.location.pathname.split("/").at(-3) : null;

        // find subject & fields & labels
        let subject = document.getElementById("id_subject");
        let tags = ["title", "answer_type", "task_count", "total_difficulty"];
        let fields = tags.map(t => document.getElementById(`id_${t}`));
        let labels = tags.map(t => document.getElementById(`id_${t}_helptext`).children[0]);


        // send request to backend, receive validation info
        function validation_part(id_sbj) {
            $.ajax({
                type: "GET",
                url: URL_VALIDATION_PART,
                data: {
                    csrfmiddlewaretoken: CSRF_TOKEN,
                    id_sbj: id_sbj,
                    id_prt: id_prt
                },
                success: function (data) {
                    validate(id_sbj, data);
                },
                error: function () {
                    console.log("validation_part() error");
                }
            });
        }

        // disable selected fields by indexes
        function disable_fields(indexes, data) {
            for (let i of indexes) {
                // add disabled attribute
                fields[i].disabled = true;
                // reset values
                fields[i].value = "";
                // change labels
                labels[i].innerHTML = data["labels"][0][i];
            }
        }

        // enable selected fields by indexes
        function enable_fields(indexes, data) {
            for (let i of indexes) {
                // remove disabled attribute
                fields[i].disabled = false;
                // calculate new values & labels
                let calcs = [
                    // 0
                    () => {
                        // value
                        let old_selected_val = fields[0].value;
                        fields[0].innerHTML = "";
                        let option = document.createElement("option");
                        option.value = "";
                        option.text = "---------";
                        fields[0].appendChild(option);
                        for (let key in data["titles"]["available"]) {
                            let option = document.createElement("option");
                            option.value = key;
                            option.text = data["titles"]["available"][key];
                            fields[0].appendChild(option);
                            if (old_selected_val === option.value)
                                option.selected = true;
                        }
                        // label
                        labels[0].innerHTML = `${data["labels"][1][0]}: [${Object.values(data["titles"]["reserved"]).join(", ")}]`;
                    },
                    // 1
                    () => {
                        // label
                        labels[1].innerHTML = data["labels"][1][1];
                    },
                    // 2
                    () => {
                        // value
                        let amount_max = data["amount"] * data["capacities"][fields[1].value];
                        let amount_min = 1 > amount_max ? 0 : 1;
                        fields[2].max = amount_max;
                        fields[2].min = amount_min;
                        let old_selected_val = fields[2].value === "" ? 0 : fields[2].value;
                        if (old_selected_val > amount_max)
                            fields[2].value = amount_max;
                        else if (old_selected_val < amount_min)
                            fields[2].value = amount_min;
                        else
                            fields[2].value = old_selected_val;
                        // label
                        if (amount_max)
                            labels[2].innerHTML = `${data["labels"][1][2]}: [${amount_min} – ${amount_max}]`;
                        else {
                            fields[2].disabled = true;
                            labels[2].innerHTML = `${data["labels"][1][2]}: [${amount_max}]`;
                        }
                    },
                    // 3
                    () => {
                        // value
                        let amount_max = fields[2].value * Object.keys(data["difficulties"]).at(-1);
                        let amount_min = 1 > amount_max ? 0 : 1 * Object.keys(data["difficulties"])[0];
                        fields[3].max = amount_max;
                        fields[3].min = amount_min;
                        fields[3].value = Math.floor(amount_max / 2);
                        if (!data["amount"] * data["capacities"][fields[1].value])
                            fields[3].disabled = true;
                        // label
                        if (amount_max)
                            labels[3].innerHTML = `${data["labels"][1][3]}: [${amount_min} – ${amount_max}]`;
                        else {
                            fields[3].disabled = true;
                            labels[3].innerHTML = `${data["labels"][1][3]}: [${amount_max}]`;
                        }
                    }
                ];
                calcs[i]();
            }
        }

        // validate all fields based on received data
        function validate(id_sbj, data) {
            // handler for subject
            id_sbj ? enable_fields([0, 1], data) : disable_fields([0, 1, 2, 3], data);
            // handler for answer_type
            fields[1].value ? enable_fields([2], data) : disable_fields([2, 3], data);
            fields[1].onchange = () => {
                fields[1].value ? enable_fields([2], data) : disable_fields([2, 3], data);
                fields[2].value ? enable_fields([3], data) : disable_fields([3], data);
            }
            // handler for task_count
            fields[2].value ? enable_fields([3], data) : disable_fields([3], data);
            fields[2].onchange = () => {
                let amount_max = data["amount"] * data["capacities"][fields[1].value];
                let amount_min = 1 > amount_max ? 0 : 1;
                fields[2].value = Math.min(fields[2].value, amount_max);
                fields[2].value = Math.max(fields[2].value, amount_min);
                fields[2].value ? enable_fields([3], data) : disable_fields([3], data);
            }
            // handler for total_difficulty
            fields[3].onchange = () => {
                let amount_max = fields[2].value * Object.keys(data["difficulties"]).at(-1);
                let amount_min = 1 > amount_max ? 0 : 1 * Object.keys(data["difficulties"])[0];
                fields[3].value = Math.min(fields[3].value, amount_max);
                fields[3].value = Math.max(fields[3].value, amount_min);
            }
        }

        // add onchange listener for subject
        let debounced_validation_part = debounce(validation_part);
        subject.onchange = () => {
            debounced_validation_part(subject.value);
        }

        // check initialized subject value
        validation_part(subject.value);

    }
});