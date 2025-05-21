import * as bootstrap from 'bootstrap';

export const handleAlerts = (alert) => {
    const container = document.getElementById("alert-container");
    if (container) {
        container.innerHTML = `
            <div class="alert alert-${alert.alert_type} mb-1 alert-dismissible fade show" role="alert">
                ${alert.alert_message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        // Initialise the alert (this ensures dismissal works)
        const alertEl = container.querySelector('.alert');
        if (alertEl) {
            new bootstrap.Alert(alertEl);
        }
    }
};
