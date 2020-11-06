var sequence_modules = {};

$(document).ready(function () {
    build_sequence_modules_layout();
});

/**
 * This function displays the alert and the given alert message by removing
 * the d-none class from the div(s).
 */
function display_alert(alert_id, alert_message) {
    $(alert_id).removeClass('d-none').html(alert_message);
}

/**
 * This function hides the alert(s) and the alert message(s) by adding the d-none
 * class to the div(s).
 */
function hide_alerts(alert_id_or_ids) {
    $(alert_id_or_ids).addClass('d-none').html('');
}

/**
 * This function gets information about the loaded sequence modules from the backend and based
 * on that, it dynamically builds and injects the HTML code for the sequence modules layout.
 */
function build_sequence_modules_layout() {
    apiGET('sequence_modules').done(function (response) {
        sequence_modules = response.sequence_modules;
        if (!jQuery.isEmptyObject(sequence_modules)) {
            // Sort the modules in alphabetical order
            sequence_modules = Object.fromEntries(Object.entries(sequence_modules).sort());
            var html_text = `<div id="accordion" role="tablist">`;
            for (seq_module in sequence_modules) {
                sequences = sequence_modules[seq_module];

                html_text += `
                <div class="row border">
                    <div class="col-md-12">
                        <div class="row">
                            <div class="col-md-12 text-center">
                                <h4><b>${seq_module}</b></h4>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-12">
                                ${build_sequences_layout(seq_module, sequences)}
                            </div>
                        </div>
                    </div>
                </div>`;
            }

            html_text += '</div>';
            $('#sequence-modules-layout').html(html_text);
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
    html_text = '';
    for (seq in sequences) {
        params = sequences[seq];

        html_text += `
        <div class="card">
            <div class="card-header" role="tab" id="${seq}-heading">
                <div class="row">
                    <div class="col-md-5">
                        <h5>`;

        sequence_params_layout = '';
        if (jQuery.isEmptyObject(params)) {
            html_text += `${seq}`;
        } else {
            html_text += `
            <a data-toggle="collapse" href="#${seq}-collapse" aria-expanded="false" aria-controls="${seq}-collapse" class="collapsed">
                ${seq}
            </a>`;
            sequence_params_layout = build_sequence_parameters_layout(seq, params);
        }

        html_text += `
                        </h5>
                    </div>
                    <div class="col-md-5">
                        <div class="sequence-alert alert alert-danger mb-0 d-none" role="alert" id="${seq}-alert"></div>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary execute-btn mb-3" onclick="execute_sequence(this)" id="${seq_module}-${seq}-execute-btn">Execute</button>
                    </div>
                </div>
            </div>
            ${sequence_params_layout}
        </div>`;
    }

    return html_text;
}

/**
 * This function builds the input boxes for all the parameters of the sequence. A
 * tooltip is added next to the parameter name label for all list parameters which
 * provides information to users about how they need to input the list elements.
 */
function build_sequence_parameters_layout(seq, params) {
    var html_text = `
    <div id="${seq}-collapse" class="collapse" role="tabpanel" aria-labelledby="${seq}-heading" data-parent="#accordion">
        <div class="card-body">`;
    for (param in params) {
        attributes = params[param];
        param_type = attributes['type'];
        param_default_value = attributes['default'];

        html_text += `
        <div class="row">
            <div class="col-md-2">
                <label for="${seq}-${param}-input">${param} (${param_type})</label>`;

        if (param_type.startsWith('list')) {
            html_text += '<i class="far fa-question-circle fa-fw my-tooltip" title="Enter elements as a comma separate string and do not include quotes or square brackets"></i>';
        }

        html_text += `
        </div>
        <div class="col-md-10">`;

        if (param_type == 'bool') {
            html_text += `
            <select class="form-control mb-3" id="${seq}-${param}-input">
                <option>False</option>
                <option>True</option>
            </select>`;
        } else {
            input_type = (param_type == 'int' || param_type == 'float') ? 'number' : 'text';
            html_text += `<input type="${input_type}" value="${param_default_value}" class="form-control mb-3" id="${seq}-${param}-input" />`;
        }

        html_text += `
            </div>
        </div>`;
    }

    html_text += `
        </div>
    </div>`;

    return html_text;
}