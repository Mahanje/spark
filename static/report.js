let reportType = null;
let reportId = null;

function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
            }
        }
    }

    return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".report-btn[data-type]").forEach(btn => {
        btn.addEventListener("click", function () {
            reportType = this.dataset.type;
            reportId = this.dataset.id;
            document.getElementById("reportModal").style.display = "flex";
        });
    });
});

function closeReportModal() {
    document.getElementById("reportModal").style.display = "none";
}

function submitReport() {
    const reason = document.getElementById("report-reason").value;
    const description = document.getElementById("report-description").value;

    fetch("/core/report/submit/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: new URLSearchParams({
            model: reportType,
            id: reportId,
            reason: reason,
            description: description
        })
    })
        .then(r => r.json())
        .then(data => {
            alert(data.message);

            if (data.status === "success") {
                closeReportModal();
            }
        });
}