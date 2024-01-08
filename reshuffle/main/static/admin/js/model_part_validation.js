// Loads jQuery
if (!$) {
    $ = django.jQuery;
}

// Function to wrap other functions, reduces the workload
function debounce(func, timeout = 100) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            func.apply(this, args);
        }, timeout);
    };
}

// On page load actions
window.addEventListener("load", () => {
    let init_load = true;
    const state = window.location.pathname.split("/").at(-2);
    if (state === "add" || state === "change") {
        // Finds subject & fields & labels
        let subject = document.getElementById("id_subject");
        let fields = [
            document.getElementById("id_title"),
            document.getElementById("id_answer_type"),
            document.getElementById("id_task_count"),
            document.getElementById("id_total_difficulty")
        ];
        let labels = [
            document.getElementById("id_title_helptext").children[0],
            document.getElementById("id_answer_type_helptext").children[0],
            document.getElementById("id_task_count_helptext").children[0],
            document.getElementById("id_total_difficulty_helptext").children[0]
        ];

        // Function to disable selected fields by indexes
        function disable_fields(indexes, data) {
            for (let i of indexes) {
                // Adds disabled attribute
                fields[i].disabled = true;
                // Resets values
                fields[i].value = "";
                // Changes labels
                labels[i].innerHTML = data["labels"][0][i];
            }
        }

        // Function to enable selected fields by indexes
        function enable_fields(indexes, data) {
            for (let i of indexes) {
                // Removes disabled attribute
                fields[i].disabled = false;
                // Resets values
                if (!init_load)
                    fields[i].value = "";
                // Sets values & changes labels
                if (data["subject"][1]) {
                    let calc_funcs = [
                        function () {
                            let old_selected_val = fields[0].value;
                            fields[0].innerHTML = "";
                            for (let key in data["titles"]["available"]) {
                                let option = document.createElement("option");
                                option.value = key;
                                option.text = data["titles"]["available"][key];
                                fields[0].appendChild(option);
                                if (old_selected_val === option.value)
                                    option.selected = true;
                            }
                            // if (JSON.stringify(data["titles"]["reserved"]) !== "{}")
                            //     labels[0].innerHTML = `${data["labels"][1][0]} [${Object.values(data["titles"]["reserved"]).join(", ")}]`;
                            // else
                            //     labels[0].innerHTML = `${data["labels"][1][0]} []`;
                        },
                        function () {
                            // labels[1].innerHTML = data["labels"][1][1];
                        },
                        function () {
                            let remained_section_count = data["counts"]["parts"];
                            for (let section of data["counts"]["reserved"]) {
                                let count = Math.ceil(section[1] / data["counts"]["cost"][Number(section[0])]);
                                remained_section_count -= count;
                                if (remained_section_count) {

                                } else {

                                }
                            }
                        },
                        function () {

                        }
                    ];
                    calc_funcs[i]();
                }
            }
        }

        // Function to send a request to the backend, receives validation info
        function validation_part(id_sbj, id_title) {
            $.ajax({
                type: "GET",
                url: URL_VALIDATION_PART,
                data: {
                    csrfmiddlewaretoken: CSRF_TOKEN,
                    id_sbj: id_sbj,
                    id_title: id_title
                },
                success: function (data) {
                    console.log(data);
                    // Handler for subject
                    id_sbj ? enable_fields([0, 1], data) : disable_fields([0, 1, 2, 3], data);
                    // Handler for answer_type
                    fields[1].value ? enable_fields([2], data) : disable_fields([2, 3], data);
                    fields[1].onchange = () => {
                        fields[1].value ? enable_fields([2], data) : disable_fields([2, 3], data);
                        fields[2].value ? enable_fields([3], data) : disable_fields([3], data);
                    }
                    // Handler for task_count
                    fields[2].value ? enable_fields([3], data) : disable_fields([3], data);
                    fields[2].onchange = () => {
                        fields[2].value ? enable_fields([3], data) : disable_fields([3], data);
                    }
                    // Changes init_load flag
                    if (init_load)
                        init_load = false;
                },
                error: function () {
                    console.log("validation_part() error");
                }
            });
        }

        // Adds "change" listener for subject
        let debounced_validation_part = debounce(validation_part);
        subject.onchange = () => {
            debounced_validation_part(subject.value, fields[0].value);
        }

        // Checks initialized subject value
        validation_part(subject.value, fields[0].value);
    }
});