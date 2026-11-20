const monitors = [

    {
        id: 1,
        name: "JSONPlaceholder",
        url: "https://jsonplaceholder.typicode.com",
        status: "UP",
        responseTime: 86,
        intervalSeconds: 60,
        history: [
            {
                status: "UP",
                statusCode: 200,
                responseTime: 86,
                checkedAt: "2026-11-13T20:30:00",
                isActive: true
            },
            {
                status: "UP",
                statusCode: 200,
                responseTime: 92,
                checkedAt: "2026-11-13T20:29:00",
                isActive: true
            },
            {
                status: "UP",
                statusCode: 200,
                responseTime: 81,
                checkedAt: "2026-11-13T20:28:00",
                isActive: true
            }
        ]
    }
];

function renderMonitors() {
    const monitorsList = document.getElementById("monitors-list");

    monitorsList.innerHTML = "";

    monitors.forEach(monitor => {
        const row = document.createElement("tr");

        const statusClass = monitor.status === "UP"
            ? "status-up"
            : "status-down";

        const responseTime = monitor.responseTime !== null
            ? `${monitor.responseTime} ms`
            : "—";

        const lastChecked = monitor.history.length > 0
            ? new Date(monitor.history[0].checkedAt).toLocaleString("ru-RU")
            : "—";

        row.innerHTML = `
            <td>${monitor.name}</td>
            <td>${monitor.url}</td>
            <td>
                <span class="monitor-status ${statusClass}">
                    ${monitor.status}
                </span>
            </td>
            <td>${responseTime}</td>
            <td>${lastChecked}</td>
            <td>
                <button class="check-btn">Проверить</button>
                <button class="toggle-btn">
                    ${monitor.isActive ? "Отключить" : "Включить"}
                </button>
                <button class="edit-btn">Изменить</button>
                <button class="delete-btn">Удалить</button>
            </td>
        `;

        monitorsList.appendChild(row);
                row.addEventListener("click", () => {
            showMonitorDetails(monitor.id);
        });

        const checkBtn = row.querySelector(".check-btn");

        const toggleBtn = row.querySelector(".toggle-btn");

        toggleBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            hideError();

            monitor.isActive = !monitor.isActive;

            renderMonitors();
        });

        checkBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            hideError();
            checkMonitor(monitor.id);
        });

        const editBtn = row.querySelector(".edit-btn");

        editBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            hideError();
            editMonitor(monitor.id);
        });

        const deleteBtn = row.querySelector(".delete-btn");

        deleteBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            hideError();

            const confirmed = confirm(
                `Удалить монитор "${monitor.name}"?`
            );

            if (!confirmed) return;

            const index = monitors.findIndex(
                item => item.id === monitor.id
            );

            monitors.splice(index, 1);

            renderMonitors();
            updateStats();
            detailsSection.classList.remove("active");
        });
    });
}

function checkMonitor(monitorId) {
    const monitor = monitors.find(
        item => item.id === monitorId
    );

    if (!monitor.isActive) return;

    // Имитируем результат проверки
    const isUp = Math.random() < 0.8;

    const responseTime = isUp
        ? Math.floor(Math.random() * 250) + 50
        : null;

    const result = {
        status: isUp ? "UP" : "DOWN",
        statusCode: isUp ? 200 : 500,
        responseTime: responseTime,
        checkedAt: new Date().toISOString()
    };

    monitor.status = result.status;
    monitor.responseTime = result.responseTime;

    // Добавляем результат в начало истории
    monitor.history.unshift(result);

    renderMonitors();
    updateStats();
}

function updateStats() {
    const totalMonitors = monitors.length;

    const upMonitors = monitors.filter(
        monitor => monitor.status === "UP"
    ).length;

    const downMonitors = monitors.filter(
        monitor => monitor.status === "DOWN"
    ).length;

    document.getElementById("total-monitors").textContent = totalMonitors;

    document.getElementById("up-monitors").textContent = upMonitors;

    document.getElementById("down-monitors").textContent = downMonitors;
}

function initDashboard() {
    renderMonitors();
    updateStats();
}

const modal = document.getElementById("monitor-modal");
const openModalBtn = document.getElementById("open-modal-btn");
const closeModalBtn = document.getElementById("close-modal-btn");
const cancelModalBtn = document.getElementById("cancel-modal-btn");
const monitorForm = document.getElementById("monitor-form");
const modalTitle = document.getElementById("modal-title");
const submitMonitorBtn = document.getElementById("submit-monitor-btn");
const errorMessage = document.getElementById("error-message");

let editingMonitorId = null;

function openModal() {
    if (editingMonitorId === null) {
        modalTitle.textContent = "Добавить монитор";
        submitMonitorBtn.textContent = "Добавить";
    }   
    modal.classList.add("active");
}

function closeModal() {
    modal.classList.remove("active");
    monitorForm.reset();

    document.getElementById("monitor-interval").value = 60;
}

function editMonitor(monitorId) {
    const monitor = monitors.find(
        item => item.id === monitorId
    );

    if (!monitor) return;

    editingMonitorId = monitor.id;

    document.getElementById("monitor-name").value = monitor.name;
    document.getElementById("monitor-url").value = monitor.url;
    document.getElementById("monitor-interval").value = monitor.intervalSeconds;
    
    modalTitle.textContent = "Редактировать монитор";
    submitMonitorBtn.textContent = "Сохранить изменения";

    openModal();
}

openModalBtn.addEventListener("click", openModal);

closeModalBtn.addEventListener("click", closeModal);

cancelModalBtn.addEventListener("click", closeModal);

modal.addEventListener("click", event => {
    if (event.target === modal) {
        closeModal();
    }
});

monitorForm.addEventListener("submit", (event) => {
    event.preventDefault();
    hideError();

    const name = document.getElementById("monitor-name").value.trim();
    const urlValue = document.getElementById("monitor-url").value.trim();
    const interval = Number(
        document.getElementById("monitor-interval").value
    );

    let url;

    try {
        url = new URL(urlValue);
    } catch {
        alert("Введите корректный URL.");
        return;
    }

    if (url.protocol !== "http:" && url.protocol !== "https:") {
        alert("Разрешены только HTTP и HTTPS адреса.");
        return;
    }

    if (!name || !url.hostname) {
        alert("Заполните все поля корректно.");
        return;
    }

    if (!Number.isInteger(interval) || interval < 30 || interval > 86400) {
        alert("Интервал должен быть от 30 до 86400 секунд.");
        return;
    }

    if (editingMonitorId !== null) {
        const monitor = monitors.find(
            item => item.id === editingMonitorId
        );

        if (monitor) {
            monitor.name = name;
            monitor.url = url.href;
            monitor.intervalSeconds = interval;
        }
    } else {
        const newMonitor = {
            id: Date.now(),
            name: name,
            url: url.href,
            intervalSeconds: interval,
            status: "DOWN",
            responseTime: null,
            history: [],
            isActive: true
        };

        monitors.push(newMonitor);
    }

    editingMonitorId = null;

    renderMonitors();
    updateStats();
    closeModal();
});

const detailsSection = document.getElementById("monitor-details");
const closeDetailsBtn = document.getElementById("close-details-btn");

function showMonitorDetails(monitorId) {
    const monitor = monitors.find(item => item.id === monitorId);

    if (!monitor) {
        return;
    }

    document.getElementById("details-name").textContent = monitor.name;
    document.getElementById("details-url").textContent = monitor.url;

    const statusElement = document.getElementById("details-status");

    statusElement.textContent = monitor.status;
    statusElement.style.color =
        monitor.status === "UP" ? "#65d6a1" : "#ff7777";

    document.getElementById("details-interval").textContent =
        `${monitor.intervalSeconds} сек.`;

    document.getElementById("details-response-time").textContent =
        monitor.responseTime !== null
            ? `${monitor.responseTime} ms`
            : "—";

    renderHistory(monitor);

    detailsSection.classList.add("active");

    detailsSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

function renderHistory(monitor) {
    const historyList = document.getElementById("history-list");

    historyList.innerHTML = "";

    (monitor.history ?? []).forEach(result => {
        const row = document.createElement("tr");

        const statusClass = result.status === "UP"
            ? "status-up"
            : "status-down";

        const checkedAt = new Date(result.checkedAt)
            .toLocaleString("ru-RU");

        row.innerHTML = `
            <td>${checkedAt}</td>
            <td>
                <span class="monitor-status ${statusClass}">
                    ${result.status}
                </span>
            </td>
            <td>${result.statusCode ?? "—"}</td>
            <td>${result.responseTime !== null
                ? `${result.responseTime} ms`
                : "—"}</td>
        `;

        historyList.appendChild(row);
    });

    if (monitor.history.length === 0) {
        historyList.innerHTML = `
            <tr>
                <td colspan="4">История проверок пока отсутствует</td>
            </tr>
        `;
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function hideError() {
    errorMessage.textContent = "";
    errorMessage.classList.add("hidden");
}

closeDetailsBtn.addEventListener("click", () => {
    detailsSection.classList.remove("active");
});

initDashboard();
