let currentPage = 0;
let pageSize = 10;
let totalElements = 0;
let totalPages = 0;
let currentRows = [];

async function loadPaymentAnomalies(page = 0) {
  const params = new URLSearchParams({ page, size: pageSize });

  try {
    const res = await fetch(`/api/adminsystem/payments/anomalies?${params.toString()}`);
    if (!res.ok) throw new Error(i18n.loadFail);

    const data = await res.json();
    currentRows = data.content || [];
    currentPage = data.number ?? page;
    totalPages = data.totalPages ?? 0;
    totalElements = data.totalElements ?? currentRows.length;

    renderRows(currentRows);
    renderSummary();
    renderPagination(totalPages, currentPage);
  } catch (err) {
    alert(err.message);
  }
}

function renderRows(rows) {
  const tbody = document.getElementById("paymentAnomalyList");
  tbody.innerHTML = "";

  if (!rows.length) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="10">${i18n.noData}</td></tr>`;
    return;
  }

  rows.forEach((row, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${currentPage * pageSize + idx + 1}</td>
      <td>${renderReasons(row.reasons)}</td>
      <td>
        <strong>${escapeHtml(row.userFullName || "-")}</strong>
        <span class="muted">${escapeHtml(row.userEmail || "")}</span>
      </td>
      <td>${escapeHtml(row.branchName || "-")}</td>
      <td>${escapeHtml(row.pitchName || "-")}</td>
      <td>
        <div>${formatMoney(row.paymentAmount)}</div>
        <span class="muted">Booking: ${formatMoney(row.bookingFinalPrice)}</span>
      </td>
      <td><span class="status-tag ${statusClass(row.paymentStatus)}">${row.paymentStatus || "-"}</span></td>
      <td><span class="status-tag ${statusClass(row.bookingStatus)}">${row.bookingStatus || "-"}</span></td>
      <td class="mono">${escapeHtml(row.txnRef || "-")}</td>
      <td><button class="btn-small btn-approve" onclick="showPaymentDetail('${row.paymentId}')">${i18n.view}</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderReasons(reasons = []) {
  return reasons.map(reason => `<span class="reason-pill">${escapeHtml(reason)}</span>`).join("");
}

function showPaymentDetail(paymentId) {
  const row = currentRows.find(item => item.paymentId === paymentId);
  if (!row) return;

  document.getElementById("modalPaymentId").textContent = row.paymentId || "-";
  document.getElementById("modalBookingId").textContent = row.bookingId || "-";
  document.getElementById("modalTxnRef").textContent = row.txnRef || "-";
  document.getElementById("modalVnpNo").textContent = row.vnpTransactionNo || "-";
  document.getElementById("modalBank").textContent = row.bankCode || "-";
  document.getElementById("modalPayDate").textContent = formatVnpPayDate(row.payDate);
  document.getElementById("modalResponse").textContent = row.responseCode || "-";
  document.getElementById("modalTransaction").textContent = row.transactionStatus || "-";
  document.getElementById("modalCreated").textContent = formatDate(row.paymentCreatedAt);
  document.getElementById("modalUser").textContent = `${row.userFullName || "-"} ${row.userEmail ? `(${row.userEmail})` : ""}`;
  document.getElementById("paymentModal").classList.add("active");
}

function closePaymentModal() {
  document.getElementById("paymentModal").classList.remove("active");
}

function renderSummary() {
  const from = totalElements === 0 ? 0 : currentPage * pageSize + 1;
  const to = Math.min((currentPage + 1) * pageSize, totalElements);
  document.getElementById("summaryText").textContent = i18n.pagination
    .replace("{0}", from)
    .replace("{1}", to)
    .replace("{2}", totalElements);
}

function renderPagination(total, current) {
  const el = document.getElementById("pagination");
  el.innerHTML = "";
  if (total <= 1) return;

  const prevDisabled = current === 0 ? "disabled" : "";
  const nextDisabled = current === total - 1 ? "disabled" : "";
  let html = `<button class="page-btn" ${prevDisabled} onclick="loadPaymentAnomalies(${current - 1})">«</button>`;

  const windowSize = 7;
  let start = Math.max(0, current - Math.floor(windowSize / 2));
  let end = Math.min(total - 1, start + windowSize - 1);
  if (end - start + 1 < windowSize) start = Math.max(0, end - windowSize + 1);

  for (let i = start; i <= end; i++) {
    html += `<button class="page-btn ${i === current ? "active" : ""}" onclick="loadPaymentAnomalies(${i})">${i + 1}</button>`;
  }

  html += `<button class="page-btn" ${nextDisabled} onclick="loadPaymentAnomalies(${current + 1})">»</button>`;
  el.innerHTML = html;
}

function changePageSize(value) {
  pageSize = parseInt(value, 10) || 10;
  loadPaymentAnomalies(0);
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString("vi-VN") + " đ";
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}

function formatVnpPayDate(value) {
  if (!value || value.length !== 14) return value || "-";
  return `${value.slice(6, 8)}/${value.slice(4, 6)}/${value.slice(0, 4)} ${value.slice(8, 10)}:${value.slice(10, 12)}:${value.slice(12, 14)}`;
}

function statusClass(status) {
  return String(status || "").toLowerCase().replaceAll("_", "-");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

window.loadPaymentAnomalies = loadPaymentAnomalies;
window.changePageSize = changePageSize;
window.showPaymentDetail = showPaymentDetail;
window.closePaymentModal = closePaymentModal;
