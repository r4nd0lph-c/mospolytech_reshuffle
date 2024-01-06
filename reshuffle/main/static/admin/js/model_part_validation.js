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
        function disable_fields(indexes) {
            for (let i of indexes) {
                // Adds disabled attribute
                fields[i].disabled = true;
                // Resets values
                // ...
                // Changes labels
                // ...
            }
        }

        // Function to send a request to the backend, receives validation info
        function validation_part(id_sbj, id_title) {
            if (!id_sbj) {
                disable_fields([0, 1, 2, 3]);
            }
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