export const handleAlerts = (alert) => {
    const container = document.getElementById("alert-container");
    if (container) {
        container.innerHTML = `
        <div class="alert alert-${alert.alert_type} mb-1" role="alert">
            ${alert.alert_message}
        </div>
        `;
    }
};