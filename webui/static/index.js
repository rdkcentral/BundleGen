var socket = io();
socket.on('connect', function () {
    socket.sendBuffer = [];
    console.log("connected");
});

socket.on('consolelog', function (msg) {
    console.log(msg);
    var currentLog = $('#consolelog').val();
    var updatedLog = currentLog + msg;
    $('#consolelog').val(updatedLog)
});

var dataTable = $('#bundles-table').DataTable({
    "columnDefs": [{ "type": "date", "targets": 0 }],
    "order": [[0, "desc"]]
});

function deleteBundle(name) {
    console.log("Delete " + name);
    $.ajax(
        {
            "url": `/bundle/${name}`,
            "type": "DELETE",
            "success": function (data) {
                loadBundles();
            },
            "error": function (xhr, status, error) {
                var err = JSON.parse(xhr.responseText);
                console.log(err);
            }
        }
    );
}

function loadBundles() {
    dataTable.clear();

    $.ajax(
        {
            "url": "/bundles",
            "type": "GET",
            "dataType": "json",
            "success": function (data) {
                $.each(data["bundles"], function (index, value) {
                    console.log(value);
                    dataTable.row.add([
                        value["date"],
                        `<code>${value["command"]}</code>`,
                        value["size"],
                        `
                        <a href="/bundle/${value["name"]}" class="button is-small is-info"><ion-icon name="cloud-download"></ion-icon></a>
                        <button class="button is-small is-danger delete-btn" data-name=${value["name"]}><ion-icon name="trash"></ion-icon></button>
                        `
                    ]
                    );
                });
                dataTable.draw();
            },
            "error": function (xhr, status, error) {
                var err = JSON.parse(xhr.responseText);
                console.log(err);
            }
        }
    );
}

$(document).ready(function () {
    $('#consolelog').val("");

    loadBundles();

    $('body').on('click', 'button.delete-btn', function () {
        deleteBundle($(this).data("name"));
    })

    $('#generateForm').on('submit', function (e) {
        $('#consolelog').val("");
        $('#generateBtn').prop("disabled", true);

        var formData = new FormData($('#generateForm')[0]);
        $.ajax(
            {
                "url": "/",
                "type": "POST",
                "data": formData,
                "processData": false,
                "contentType": false,
                "dataType": "json",
                "success": function (data) {
                    loadBundles();
                    Swal.fire({
                        title: 'Success!',
                        text: 'Successfully generated bundle',
                        icon: 'success'
                    });

                    $('#generateBtn').prop("disabled", false);
                },
                "error": function (xhr, status, error) {
                    var err = JSON.parse(xhr.responseText);
                    Swal.fire({
                        title: 'Something went wrong',
                        text: `Failed to generate bundle with error: ${err["message"]}`,
                        icon: 'error'
                    });

                    $('#generateBtn').prop("disabled", false);
                }
            }
        );

        e.preventDefault();
        return false;
    });

    const fileInput = document.querySelector('#image_file_upload input[type=file]');
    fileInput.onchange = () => {
        if (fileInput.files.length > 0) {
            const fileName = document.querySelector('#image_file_upload .file-name');
            fileName.textContent = fileInput.files[0].name;

            $('#image_url').val("");
            $('#image_url').prop("disabled", true);
        }
    }
});