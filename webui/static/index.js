/*
* If not stated otherwise in this file or this component's license file the
* following copyright and licenses apply:
*
* Copyright 2020 Consult Red
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

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
                        `<code>${value["name"]}</code>`,
                        `<code>${value["command"]}</code>`,
                        `${value["size"]}M`,
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

function setFilename(fileInput) {
    const fileName = document.querySelector('#image_file_upload .file-name');
    if (fileInput.files.length > 0) {
        if (fileInput.files[0].name.length > 70)
        {
            fileName.textContent = fileInput.files[0].name.substring(0, 70) + "...";
        }
        else
        {
            fileName.textContent = fileInput.files[0].name;
        }

        $('#image_url').val("");
        $('#image_url').prop("disabled", true);
    }
    else
    {
        fileName.textContent = "...";
        $('#image_url').val("");
        $('#image_url').prop("disabled", false);
    }
}

$(document).ready(function () {
    $('#consolelog').val("");

    loadBundles();

    $('body').on('click', 'button.delete-btn', function () {
        deleteBundle($(this).data("name"));
    });

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
    setFilename(fileInput);

    fileInput.onchange = () => {
        setFilename(fileInput);
    }

    $('#clear-file-btn').on('click', function () {
        fileInput.value = "";
        setFilename(fileInput);
    });
});
