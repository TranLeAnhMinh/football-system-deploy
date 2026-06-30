async function loadAdminVouchers() {
    const container = document.getElementById("voucherContainer");
    container.innerHTML = `<p class="loading-text">${i18n.loading}</p>`;

    const token = localStorage.getItem("accessToken");
    if (!token) {
        container.innerHTML = `<p class="error-text">${i18n.error}</p>`;
        return;
    }

    try {
        const res = await fetch("/api/adminsystem/vouchers", {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) {
            container.innerHTML = `<p class="error-text">${i18n.error}</p>`;
            return;
        }

        const vouchers = await res.json();

        if (!vouchers || vouchers.length === 0) {
            container.innerHTML = `<p class="empty-text">${i18n.empty}</p>`;
            return;
        }

        const html = vouchers.map(v => `
            <div class="voucher-card">
                <div class="voucher-left">
                    <h4 class="voucher-code">${v.code}</h4>

                    <div class="voucher-info">
                        <div><strong>${i18n.voucherType}:</strong> ${v.type}</div>
                        <div><strong>${i18n.voucherValue}:</strong> ${formatValue(v)}</div>
                        <div><strong>${i18n.voucherMinOrder}:</strong> ${formatMoney(v.minOrder)}</div>
                        <div><strong>${i18n.voucherMaxDiscount}:</strong> ${formatMoney(v.maxDiscount)}</div>
                        <div>
                            <strong>${i18n.voucherTime}:</strong>
                            ${formatDate(v.startAt)} → ${formatDate(v.endAt)}
                        </div>
                    </div>
                </div>

                <div class="voucher-right">
                    ${
                        v.active
                            ? `<span class="status-tag active">${i18n.statusActive}</span>`
                            : `<span class="status-tag inactive">${i18n.statusInactive}</span>`
                    }

                    <div class="voucher-actions">
                        <button class="btn-edit"
                                title="${i18n.edit}"
                                onclick='openEditVoucherModalFromEncoded("${encodeURIComponent(JSON.stringify(v))}")'>
                            <i class="fa fa-pen"></i>
                        </button>

                        <button class="${v.active ? "btn-delete" : "btn-activate"}"
                                title="${v.active ? i18n.confirmDisable : i18n.confirmEnable}"
                                onclick="toggleVoucherActive('${v.id}')">
                            <i class="fa ${v.active ? "fa-ban" : "fa-rotate-left"}"></i>
                        </button>

                        <button class="btn-hard-delete"
                                title="${i18n.confirmHardDelete}"
                                onclick="hardDeleteVoucher('${v.id}')">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join("");

        container.innerHTML = html;

    } catch (err) {
        console.error(err);
        container.innerHTML = `<p class="error-text">${i18n.error}</p>`;
    }
}

/* ================= OPEN EDIT MODAL ================= */
function openEditVoucherModalFromEncoded(encoded) {
    const v = JSON.parse(decodeURIComponent(encoded));
    openEditVoucherModal(v);
}

function openEditVoucherModal(v) {
    const form = document.getElementById("editVoucherForm");

    form.voucherId.value = v.id;
    form.code.value = v.code || "";
    form.type.value = v.type || "PERCENT";
    form.value.value = v.value ?? "";
    form.minOrder.value = v.minOrder ?? "";
    form.maxDiscount.value = v.maxDiscount ?? "";
    form.startAt.value = toDatetimeLocal(v.startAt);
    form.endAt.value = toDatetimeLocal(v.endAt);
    form.perUserLimit.value = v.perUserLimit ?? 1;

    new bootstrap.Modal(
        document.getElementById("editVoucherModal")
    ).show();
}

/* ================= UPDATE ================= */
document.getElementById("editVoucherForm")
    .addEventListener("submit", async (e) => {
        e.preventDefault();

        const form = e.target;
        const token = localStorage.getItem("accessToken");
        const voucherId = form.voucherId.value;

        const payload = {
            code: form.code.value,
            type: form.type.value,
            value: Number(form.value.value),
            minOrder: Number(form.minOrder.value || 0),
            maxDiscount: Number(form.maxDiscount.value || 0),
            startAt: new Date(form.startAt.value).toISOString(),
            endAt: new Date(form.endAt.value).toISOString(),
            perUserLimit: Number(form.perUserLimit.value || 1)
        };

        try {
            const res = await fetch(`/api/adminsystem/vouchers/${voucherId}`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                alert(i18n.updateFail);
                return;
            }

            bootstrap.Modal
                .getInstance(document.getElementById("editVoucherModal"))
                .hide();

            form.reset();
            loadAdminVouchers();

        } catch (err) {
            console.error(err);
            alert(i18n.updateFail);
        }
    });

/* ================= TOGGLE ACTIVE / INACTIVE ================= */
async function toggleVoucherActive(id) {
    const token = localStorage.getItem("accessToken");
    if (!token) {
        alert(i18n.error);
        return;
    }

    if (!confirm(i18n.confirmToggle)) return;

    try {
        const res = await fetch(`/api/adminsystem/vouchers/${id}/toggle-active`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!res.ok) {
            alert(i18n.toggleFail);
            return;
        }

        loadAdminVouchers();

    } catch (err) {
        console.error(err);
        alert(i18n.toggleFail);
    }
}

/* ================= HARD DELETE ================= */
async function hardDeleteVoucher(id) {
    const token = localStorage.getItem("accessToken");
    if (!token) {
        alert(i18n.error);
        return;
    }

    if (!confirm(i18n.confirmHardDelete)) return;

    try {
        const res = await fetch(`/api/adminsystem/vouchers/${id}/hard`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!res.ok) {
            alert(i18n.hardDeleteFail);
            return;
        }

        loadAdminVouchers();

    } catch (err) {
        console.error(err);
        alert(i18n.hardDeleteFail);
    }
}

/* ================= CREATE ================= */
document.getElementById("createVoucherForm")
    .addEventListener("submit", async (e) => {
        e.preventDefault();

        const form = e.target;
        const token = localStorage.getItem("accessToken");

        const payload = {
            code: form.code.value,
            type: form.type.value,
            value: Number(form.value.value),
            minOrder: Number(form.minOrder.value || 0),
            maxDiscount: Number(form.maxDiscount.value || 0),
            startAt: new Date(form.startAt.value).toISOString(),
            endAt: new Date(form.endAt.value).toISOString(),
            perUserLimit: Number(form.perUserLimit.value || 1)
        };

        try {
            const res = await fetch("/api/adminsystem/vouchers", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                alert(i18n.createFail);
                return;
            }

            bootstrap.Modal
                .getInstance(document.getElementById("createVoucherModal"))
                .hide();

            form.reset();
            loadAdminVouchers();

        } catch (err) {
            console.error(err);
            alert(i18n.createFail);
        }
    });

function formatMoney(val) {
    if (val == null) return "-";
    return Number(val).toLocaleString("vi-VN");
}

function formatDate(iso) {
    if (!iso) return "-";
    const d = new Date(iso);
    return d.toLocaleDateString("vi-VN");
}

function formatValue(v) {
    if (v.type === "PERCENT") {
        return `${v.value}%`;
    }
    return formatMoney(v.value);
}

function toDatetimeLocal(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    const offset = d.getTimezoneOffset();
    const local = new Date(d.getTime() - offset * 60000);
    return local.toISOString().slice(0, 16);
}