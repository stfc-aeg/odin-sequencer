let detect_module_modifications;
let last_message_timestamp = '';
let sequence_modules = {};
let is_executing;
let sequencer_endpoint;
let detect_changes_switch  = document.getElementById('detect-module-changes-toggle');
let execution_spinner = document.getElementById("execution-status-spinner");
let execution_text = document.getElementById("execution-status-text");
let execution_progress = document.getElementById("execution-progress");
let execution_progress_bar = document.getElementById("execution-progress-bar");
let execution_status_progress = document.getElementById("execution-status-progress");
var changing_params = {};

const ALERT_ID = {
    'sequencer_error': '#command-sequencer-error-alert',
    'sequencer_info': '#command-sequencer-info-alert',
};

const BUTTON_ID = {
    'all_execute': '.execute-btn',
    'reload': '#reload-btn',
    'abort': '#abort-btn'
};

/**
 * This function is called when the DOM content of the page is loaded, and initialises
 * various elements of the sequencer page. The sequence module layout and log messages
 * are initialised from the current state of the adapter and the current execution state
 * is retrieved and managed appropriately.
 */
document.addEventListener("DOMContentLoaded", function () {

    // Initialise the sequencer adapter endpoint
    sequencer_endpoint = new AdapterEndpoint("odin_sequencer");

    build_sequence_modules_layout();
    display_log_messages();

    sequencer_endpoint.get('')
    .then(result => {
        is_executing = result.is_executing;
        detect_module_modifications = result.detect_module_modifications;

        if (is_executing) {
            disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);
            disable_buttons(`${BUTTON_ID['abort']}`, false);
            display_execution(result.execute);
            await_execution_complete();
            await_process_execution_complete();
        }
        else
        {
            disable_buttons(`${BUTTON_ID['abort']}`, true);
            hide_execution();
        }

        set_detect_module_changes_toggle(detect_module_modifications);
        if (detect_module_modifications) {
            await_module_changes();
        }
    })
    .catch(error => {
        display_alert(ALERT_ID['sequencer_error'], error.message);
    });
});


/**
 * This is called when a change in the Detect Changes toggle is detected. Depending on
 * whether the toggle was enabled or disabled, it calls the mechanism on the backend to
 * either enable or disable the detect module changes process. If the toggle is enabled,
 * it calls the await_module_changes function to listen for module changes. It also
 * displays an alert message if an error occurs.
 */
detect_changes_switch.addEventListener("change", function() {
    enabled = detect_changes_switch.checked;
    sequencer_endpoint.put({ 'detect_module_modifications': enabled })
    .then(() => {
        detect_module_modifications = enabled;
        if (enabled) {
            await_module_changes();
        }
    })
    .catch(error => {
        if (enabled) {
            set_detect_module_changes_toggle(false);
        }
        display_alert(ALERT_ID['sequencer_error'], error.message);
    });
});

/**
 * This function listens for module changes by calling itself every second. It displays
 * an alert message when it detects that the backend has reported of module changes. 
 */
function await_module_changes() {
    sequencer_endpoint.get('module_modifications_detected')
    .then(result => {
        if (result.module_modifications_detected) {
            info_message = 'Code changes were detected, click the Reload button to load them';
            display_alert(ALERT_ID['sequencer_info'], info_message);
        }

        if (detect_module_modifications) {
            setTimeout(await_module_changes, 1000);
        }
    })
    .catch(error => {
        display_alert(ALERT_ID['sequencer_error'], error.message);
    });
}

/**
 * This function enables or disables the Detect Changes toggle.
 */
function set_detect_module_changes_toggle(detect_module_modifications) {
    detect_changes_switch.checked = detect_module_modifications;
}

/**
 * This function calls the reloading mechanism implemented on the backend which decides
 * which modules need to be reloaded. It disables the execute and reload buttons before
 * making a call to the backend and enables them when the process completes or fails.
 * It also calls the build_sequence_modules_layout to rebuild the layout and displays
 * the relevant messages in the alerts depending on the process outcome.
 */
function reload_modules() {
    hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']}`);
    disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);

    alert_id = '';
    alert_message = '';
    sequencer_endpoint.put({ 'reload': true })
    .then(() => {
        alert_id = ALERT_ID['sequencer_info'];
        alert_message = 'The sequence modules were successfully reloaded';
    })
    .catch(error => {
        alert_id = ALERT_ID['sequencer_error'];
        alert_message = error.message
        if (!alert_message.startsWith('Cannot start the reloading')) {
            alert_message += '.<br><br>To load the missing sequences, first resolve the errors and then click the Reload button.';
        }
    })
    .then(() => {
        display_alert(alert_id, alert_message);
        build_sequence_modules_layout();
        disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, false);
    });
}

function abort_sequence() {
    hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']}`);

    alert_id = '';
    alert_message = '';
    sequencer_endpoint.put({ 'abort': true })
    .then(() => {
        alert_id = ALERT_ID['sequencer_info'];
        alert_message = "Abort sent to currently executing sequence";
    })
    .catch(error => {
        alert_id = ALERT_ID['sequencer_error'];
        alert_message = error.message;
    })
    .then(() => {
        display_alert(alert_id, alert_message);
    });
}
/**
 * This function replicates the equivalent jQuery isEmptyObject, returning true if the
 * object passed as an parameter is empty.
 */
function is_empty_object(obj) {
    return Object.keys(obj).length === 0;
}

/**
 * This function executes a sequence. Each sequence in the UI has an Execute button
 * whose id contains the name of the sequence, and it decides which sequence to execute
 * based on the id. If the sequence has parameter(s) then it will get input values and
 * send them to the back end before executing it. Because the execute call to the
 * backend is asynchronous, it calls the await_execution_complete function with a
 * slight delay. It also disables the execute and reload buttons, and displays
 * messages in the alerts about any errors that may occur during the processes.
 */
function execute_sequence(button) {
    clicked_button_id = button.id;
    arr = clicked_button_id.split('-');
    seq_module_name = arr[0];
    seq_name = arr[1];
    params = sequence_modules[seq_module_name][seq_name];

    if (!is_empty_object(params)) {
        
        data = get_input_parameter_values(params);
        
        sequencer_endpoint.put(data, `sequence_modules/${seq_module_name}/${seq_name}`)
        .then(() => {
            hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']},.sequence-alert`);
            disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);
            disable_buttons(`${BUTTON_ID['abort']}`, false);
            display_execution(`${seq_module_name}/${seq_name}`);

            sequencer_endpoint.put({ 'execute': seq_name })
            .catch(error => {
                alert_message = error.message;
                if (alert_message.startsWith('Invalid list')) {
                    alert_message = alert_message.substring(alert_message.lastIndexOf(':') + 2);
                }

                display_alert(`#${seq_name}-alert`, alert_message);
            });

            setTimeout(await_execution_complete, 250);
            setTimeout(await_process_execution_complete, 500);
        })
        .catch(error => {
            alert_message = error.message;
            if (alert_message.startsWith('Type mismatch updating')) {
                last_slash = alert_message.lastIndexOf('/');
                second_to_last_slash = alert_message.lastIndexOf('/', last_slash - 1);
                param_name = alert_message.substring(second_to_last_slash + 1, last_slash);
                alert_message = `${param_name} - ${alert_message.substring(alert_message.lastIndexOf(':') + 2)}`;
            }

            display_log_messages();
            display_alert(`#${seq_name}-alert`, alert_message);
        });

    } else {
        disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);
        disable_buttons(`${BUTTON_ID['abort']}`, false);
        display_execution(`${seq_module_name}/${seq_name}`);
        sequencer_endpoint.put({ 'execute': seq_name })
        .catch(error => {
            alert_message = error.message;
            display_alert(`#${seq_name}-alert`, alert_message);
        });

        setTimeout(await_execution_complete, 250);
        setTimeout(await_process_execution_complete, 500);
        
    }
}

/**
 * This function gets the input parameter values. The id of each parameter
 * input box contains the name of the parameter. It calls the parse_parameter_value
 * function if the parameter type is not of type string.
 */
function get_input_parameter_values(params, seq) {
    data = {};
    for (param in params) {
        param_val = document.querySelector(`#${seq_name}-${param}`).value;
        param_type = params[param]['type'];

        if (param_type != 'str') {
            param_val = parse_parameter_value(param_val, param_type);
        }

        data[param] = { 'value': param_val };
    }

    return data;
}

function getNestedProperty(obj, path) {
    return path.split('.').reduce((acc, part) => acc && acc[part], obj)
}

function save_changes(seq, seq_module) {

    seq_module = getNestedProperty(sequence_modules, seq_module)
    params = getNestedProperty(seq_module, seq)

    for (param in params) {
        params[param].value = (document.querySelector(`#${seq}-${param}`)).value
    }
}

function cancel_changes(seq, seq_module) {

    first_seq_module = getNestedProperty(sequence_modules, seq_module)
    first_params = getNestedProperty(first_seq_module, seq)
   
    for (param in first_params) {
        (document.querySelector(`#${seq}-${param}`)).value = first_params[param].value
    }
}

function params_checker() {
    changing_params = sequence_modules
}


/**
 * This function parses the parameter value from string to the correct type.
 * Parsing is required because input boxes hold values in form of strings.
 * If the parameter is of type list, then the string is split by comma to
 * form an array of strings.
 */
function parse_parameter_value(param_val, param_type) {
    if (param_type.startsWith('list')) {
        const element_type = param_type.split("list-");
        param_val = param_val.split(',');

        return param_val.map(function (element) {
            return parse_parameter_value(element.trim(), element_type[1]);
        })
    }

    switch (param_type) {
        case 'int':
            param_val = parseInt(param_val);
            break;
        case 'float':
            param_val = parseFloat(param_val);
            break;
        case 'bool':
            param_val = param_val.toLowerCase() == 'true';
            break;
    }

    return param_val;
}

/**
 * This function waits for the execution to complete by calling itself if the process
 * is not finished. It calls the display_log_messages to display any log messages.
 * It enables the execute and reload buttons when it detects that the execution
 * process has completed.
 */
function await_execution_complete() {
    sequencer_endpoint.get('is_executing')
    .then(result => {
        display_log_messages();
        is_executing = result.is_executing
        if (is_executing) {
            update_execution_progress();
            setTimeout(await_execution_complete, 500);
        } else {
            disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, false);
            disable_buttons(`${BUTTON_ID['abort']}`, true);
            hide_execution();
        }
    });
}

/**
 * This function waits for the execution of a process task to complete by calling
 * itself if the process is not finished. It calls the display_log_messages to 
 * display any log messages.
 */
function await_process_execution_complete() {
    sequencer_endpoint.get('process_tasks')
    .then(result => {
        display_log_messages();
        process_tasks = result.process_tasks
        if (process_tasks.length != 0) {
            setTimeout(await_process_execution_complete, 500);
        }
    });
}

/**
 * This function displays the alert and the given alert message by removing
 * the d-none class from the div(s).
 */
function display_alert(alert_id, alert_message) {
    let alert_elem = document.querySelector(alert_id);
    alert_elem.innerHTML = alert_message;
    alert_elem.classList.remove('d-none');
}

/**
 * This function hides the alert(s) and the alert message(s) by adding the d-none
 * class to the div(s).
 */
function hide_alerts(alert_id_or_ids) {
    alert_elems = document.querySelectorAll(alert_id_or_ids);
    alert_elems.forEach(element => {
        element.innerHTML = '';
        element.classList.add('d-none');
    });
    //$(alert_id_or_ids).addClass('d-none').html('');
}

/*
 * This function displays the excution progress elements on the UI
 */
function display_execution(sequence_name)
{
    execution_spinner.classList.remove('d-none');
    execution_text.innerHTML = "<b>Executing:&nbsp;" + sequence_name + "</b>";
    execution_progress_bar.style.width = "0%";
    execution_progress_bar.setAttribute('aria-valuenow', 0);
    execution_status_progress.innerHTML = ""

    execution_progress.classList.remove('d-none');
}

/*
 * This function hides the eexcution progress elements on the UI
 */
function hide_execution()
{
    execution_progress.classList.add('d-none');
    execution_spinner.classList.add('d-none');
    execution_text.innerHTML = "";
    execution_status_progress.innerHTML = "";
}

/*
 * This function updates the execution progress bar
 */

function update_execution_progress()
{
    sequencer_endpoint.get('execution_progress')
    .then(result => {
        var current = result.execution_progress.current;
        var total = result.execution_progress.total;
        if (total != -1)
        {
            var percent_complete = Math.floor((100.0 * current) / total);
            execution_progress_bar.style.width = percent_complete + "%";
            execution_progress_bar.setAttribute('aria-valuenow', percent_complete);
            execution_status_progress.innerHTML = "<b>(" + current + "/" + total + ")</b>";
        }
        else
        {
            execution_progress_bar.style.width = "100%";
            execution_status_progress.innerHTML = "";
        }
    });
}

/**
 * This function disables the button(s) if disabled is True, otherwise it enables them.
 */
function disable_buttons(button_id_or_ids, disabled) {
    button_elems = document.querySelectorAll(button_id_or_ids)
    button_elems.forEach(element => {
        element.disabled = disabled;
    });
    //$(button_id_or_ids).prop('disabled', disabled);
}

/**
 * This function extracts the message from the error response. 
 */
function extract_error_message(jqXHR) {
    response_text = JSON.parse(jqXHR["responseText"]);
    return response_text['error'];
}

/**
 * This function displays the log messages that are returned by the backend in the
 * pre-scrollable element and scrolls down to the bottom of it. It stores the
 * timestamp of the last message so that it can tell the backend which messages it
 * needs to get next. All log messages are returned if the last_message_timestamp is
 * empty and this normally happens when the page is reloaded.
 */
function display_log_messages() {
    get_log_messages()
    .then(result => {
        log_messages = result.log_messages;
        if (!is_empty_object(log_messages)) {
            last_message_timestamp = log_messages[log_messages.length - 1][0];

            pre_scrollable = document.querySelector('#log-messages');
            for (log_message in log_messages) {
                timestamp = log_messages[log_message][0];
                timestamp = timestamp.substr(0, timestamp.length - 3);
                pre_scrollable.innerHTML += 
                    `<span style="color:#007bff">${timestamp}</span> ${log_messages[log_message][1]}<br>`;
                pre_scrollable.scrollTop = pre_scrollable.scrollHeight;
            }
        }
    })
    .catch(error => {
        alert_message = 'A problem occurred while trying to get log messages: ' + error.message;
        display_alert(ALERT_ID['sequencer_info'], alert_message);
    });
}

/**
 * This function gets the log messages from the backend.
 */
function get_log_messages() {
    return sequencer_endpoint.put({ 'last_message_timestamp': last_message_timestamp })
        .then(sequencer_endpoint.get('log_messages')
    );
}

/**
 * This function gets information about the loaded sequence modules from the backend and based
 * on that, it dynamically builds and injects the HTML code for the sequence modules layout.
 */
function build_sequence_modules_layout() {
    sequencer_endpoint.get('sequence_modules')
    .then(result => {
        
        sequence_modules = result.sequence_modules;

        if (!is_empty_object(sequence_modules)) {
            // Sorts the modules in alphabetical order
            sequence_modules = Object.fromEntries(Object.entries(sequence_modules).sort());
            let html_text = `<div class="accordion" id="module-accordion">`;

            // Creates an accordion-item for every sequence module
            for (seq_module in sequence_modules) {
                sequences = sequence_modules[seq_module];

                html_text += `
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="${seq_module}-acc">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${seq_module}-collapse" aria-expanded="true" aria-controls="collapse-${seq_module}">
                                ${seq_module}
                            </button>
                        </h2>
                        <div id="collapse-${seq_module}" class="accordion-collapse collapse show" aria-labelledby="${seq_module}-acc" data-bs-parent="#module-accordian"
                            <div class="accordion-body">
                                ${build_sequences_layout(seq_module, sequences)}
                            </div>
                        </div>
                    </div>
                    </div>`;
            }

            html_text += '</div>';
            document.querySelector('#sequence-modules-layout').innerHTML = html_text;
        } else {
            error_message = 'There are no sequence modules loaded';
            display_alert(ALERT_ID['sequencer_info'], error_message);
        }
    });
}

/**
 * This function builds the sequences layout for each module. It creates a collapsable
 * element if the sequence has parameters. 
 */
function build_sequences_layout(seq_module, sequences) {
    let html_text = `
    <div id="${seq_module}-collapse" class="collapse" role="tabpanel" aria-labelledby="${seq_module}-heading" data-parent="#accordion" style="padding: 0px">
        <div class="row">
        `;

    // Creates a card for every sequence within a module
    for (seq in sequences) {
        params = sequences[seq];

        sequence_params_layout = build_sequence_parameters_layout(seq, params)

        html_text +=    `<div class="col col-card" style="padding:0;">
                        <div class="row">
                        <div class="card card-new" style="padding:0px">
                            <div class="card-body" style="padding:4px">
                                <h6 class="card-title text-center">${String(seq).replaceAll("_", " ")}</h6>
                                <div class="row" style="padding:0px">
                        `

        // Only creates a parameters modal if there are parameters to be changed
        if (!is_empty_object(params)) {
            html_text += `<div class="col" style="padding:0">
                            <button type="button" data-bs-toggle="modal" data-bs-target="#${seq_module}-${seq}-modal" onclick="params_checker()" class="btn btn-info">Parameters</button>
                            <div class="modal" id="${seq_module}-${seq}-modal" tabindex="-1" role="dialog" aria-labelledby="${seq_module}-${seq}-modal-label" aria-hidden="true" style="height: 500px">
                                <div class="modal-dialog" role="document">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <div class="modal-title" id="${seq_module}-${seq}-modal-label">${seq}</div>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="close" onclick="cancel_changes(${("'"+String(seq)+"'")}, ${"'"+String(seq_module)+"'"})"></button>
                                        </div>
                                        <div class="modal-body">
                                            ${sequence_params_layout}
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" onclick="cancel_changes(${("'"+String(seq)+"'")}, ${"'"+String(seq_module)+"'"})">Close</button>
                                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" onclick="save_changes(${("'"+String(seq)+"'")}, ${"'"+String(seq_module)+"'"})">Save Changes</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>`
        } else {
            html_text += `<div class="col">
                        </div>`            
        }


        html_text +=   `<div class="col" style="padding:0">
                            <div class="row justify-content-end">

                            <button type="button" data-bs-dismiss="modal" class="btn btn-success btn-width" onclick="execute_sequence(this)" id="${seq_module}-${seq}-execute-btn">Execute</button>
                        </div>
                        </div>
                    </div>
                </div>
                </div>
            </div>
        </div>
        `    
    }   
    html_text += `
        </div>
    </div>
        `

    return html_text;
}

/**
 * This function builds the input boxes for all the parameters of the sequence. A
 * tooltip is added next to the parameter name label for all list parameters which
 * provides information to users about how they need to input the list elements.
 */

function build_sequence_parameters_layout(seq, params) {

    let html_text = ``

    for (param in params) {
        attributes = params[param];
        param_type = attributes['type'];
        param_default_value = attributes['default'];

        html_text += `
        <div class="row">
            <div class="col-md-4">
                <label for="${seq}-${param}">${param} (${param_type})</label>`;

        if (param_type.startsWith('list')) {
            html_text += '<i class="far fa-question-circle fa-fw my-tooltip" title="Enter elements as a comma separate string and do not include quotes or square brackets"></i>';
        }

        html_text += `
        </div>
        <div class="col-md-8">`;

        if (param_type == 'bool') {
            html_text += `
            <select class="form-control mb-3" id="${seq}-${param}">
                <option>False</option>
                <option>True</option>
            </select>`;
        } else {
            input_type = (param_type == 'int' || param_type == 'float') ? 'number' : 'text';
            html_text += `<input type="${input_type}" value="${param_default_value}" class="form-control mb-3" id="${seq}-${param}" />`;
        }

        html_text += `
        </div>
        </div>`;
    }

    return html_text;
}