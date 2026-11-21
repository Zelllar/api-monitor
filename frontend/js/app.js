let monitors = [];
let openedMonitorId = null;
let isRefreshing = false;

const API_URL = "http://127.0.0.1:8000/api";

async function fetchMonitors() {
    
    if (isRefreshing) return;

    isRefreshing = true;

    try {
        const response = await fetch(`${API_URL}/monitors`);

        if (!response.ok) {
            throw new Error("Не удалось загрузить мониторы");
        }

        monitors = await response.json();

        await Promise.all(
            monitors.map(async (monitor) => {
                const historyResponse = await fetch(
                    `${API_URL}/monitors/${monitor.id}/history`
                );

                if (!historyResponse.ok) {
                    throw new Error(
                        `Не удалось загрузить историю монитора ${monitor.id}`
                    );
                }

                monitor.history = await historyResponse.json();

                const lastCheck = monitor.history[0];

                monitor.status = lastCheck?.status ?? "UNKNOWN";
                monitor.responseTime = lastCheck?.responseTimeMs ?? null;
            })
        );

        renderMonitors();
        updateStats();

        if (openedMonitorId !== null) {
            showMonitorDetails(openedMonitorId, false);
        }

    } catch (error) {
        handleApiError(error);
    } finally {
        isRefreshing = false;
    }
}

setInterval(() => {
    if (!document.hidden) {
        fetchMonitors();
    }
}, 15000);

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

        const lastChecked = monitor.history?.length > 0
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

        toggleBtn.addEventListener("click", async (event) => {
            event.stopPropagation();

            try {
                const response = await fetch(
                    `${API_URL}/monitors/${monitor.id}`,
                    {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            isActive: !monitor.isActive
                        })
                    }
                );

                if (!response.ok) {
                    throw new Error("Не удалось изменить статус монитора");
                }

                await fetchMonitors();
                hideError();

            } catch (error) {
                handleApiError(error);
            }
        });

        checkBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            checkMonitor(monitor.id);
        });

        const editBtn = row.querySelector(".edit-btn");

        editBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            editMonitor(monitor.id);
        });

        const deleteBtn = row.querySelector(".delete-btn");

        deleteBtn.addEventListener("click", async (event) => {
            event.stopPropagation();
            hideError();

            const confirmed = confirm(
                `Удалить монитор "${monitor.name}"?`
            );

            if (!confirmed) return;

            try {
                const response = await fetch(
                    `${API_URL}/monitors/${monitor.id}`,
                    {
                        method: "DELETE"
                    }
                );

                if (!response.ok) {
                    throw new Error("Не удалось удалить монитор");
                }

                detailsSection.classList.remove("active");

                await fetchMonitors();

            } catch (error) {
                handleApiError(error);
            }
        });
    });
}

async function checkMonitor(monitorId) {
    const monitor = monitors.find(
        item => item.id === monitorId
    );

    if (!monitor || !monitor.isActive) return;

    try {
        const response = await fetch(
            `${API_URL}/monitors/${monitorId}/check`,
            {
                method: "POST"
            }
        );

        if (!response.ok) {
            throw new Error("Не удалось выполнить проверку монитора");
        }

        hideError();
        await fetchMonitors();
        showMonitorDetails(monitorId, false);

    } catch (error) {
        handleApiError(error);
    }
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
    fetchMonitors();
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

monitorForm.addEventListener("submit", async (event) => {
    event.preventDefault();

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

    try {
        if (editingMonitorId !== null) {
            const response = await fetch(
                `${API_URL}/monitors/${editingMonitorId}`,
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        name: name,
                        url: url.href,
                        intervalSeconds: interval
                    })
                }
            );

            if (!response.ok) {
                throw new Error("Не удалось обновить монитор");
            }

        } else {
            const response = await fetch(`${API_URL}/monitors`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name,
                    url: url.href,
                    intervalSeconds: interval
                })
            });

            if (!response.ok) {
                throw new Error("Не удалось создать монитор");
            }
        }

        hideError();
        editingMonitorId = null;
        closeModal();
        await fetchMonitors();

    } catch (error) {
        handleApiError(error);
    }
});

const detailsSection = document.getElementById("monitor-details");
const closeDetailsBtn = document.getElementById("close-details-btn");

function showMonitorDetails(monitorId, shouldScroll = true) {
    const monitor = monitors.find(item => item.id === monitorId);

    if (!monitor) {
        return;
    }

    openedMonitorId = monitorId;

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

    if (!detailsSection.classList.contains("active")) {
        detailsSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }
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
        <td>${result.errorMessage ?? "—"}</td>
        <td>${result.responseTimeMs != null
            ? `${result.responseTimeMs} ms`
            : "—"}</td>
    `;

        historyList.appendChild(row);
    });

    if (monitor.history.length === 0) {
        historyList.innerHTML = `
            <tr>
                <td colspan="5">История проверок пока отсутствует</td>
            </tr>
        `;
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function handleApiError(error) {
    if (error instanceof TypeError) {
        showError(
            "Не удалось подключиться к серверу. Возможно, он временно недоступен. Попробуйте позже."
        );
        return;
    }

    showError(error.message);
}

function hideError() {
    errorMessage.textContent = "";
    errorMessage.classList.add("hidden");
}

closeDetailsBtn.addEventListener("click", () => {
    detailsSection.classList.remove("active");
});

initDashboard();
