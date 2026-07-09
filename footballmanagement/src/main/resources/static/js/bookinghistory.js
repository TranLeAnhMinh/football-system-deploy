let currentPage = 0;
let pageSize = 10;
let totalElements = 0;
let totalPages = 0;
let currentBookings = [];

async function loadBookingHistory(page = 0) {
  try {
    const res = await fetch(`/api/bookings/history?page=${page}&size=${pageSize}`);
    if (!res.ok) throw new Error("Không thể tải lịch sử đặt sân");

    const data = await res.json();
    const rows = data.content || [];
    currentBookings = rows;
    currentPage = data.number ?? page;
    totalPages = data.totalPages ?? 0;
    totalElements = data.totalElements ?? rows.length;

    renderRows(rows);
    renderSummary();
    renderPagination(totalPages, currentPage);
  } catch (e) {
    alert(e.message);
  }
}

function renderRows(items) {
  const tbody = document.getElementById("bookingList");
  tbody.innerHTML = "";

  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:#64748b;">${bookingNoDataText}</td></tr>`;
    return;
  }

  items.forEach((b, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${currentPage * pageSize + idx + 1}</td>
      <td>${escapeHtml(b.pitchName || "-")}</td>
      <td>${escapeHtml(b.branchName || "-")}</td>
      <td>${formatDate(b.createdAt)}</td>
      <td><span class="status ${statusClass(b.status)}">${mapStatus(b.status)}</span></td>
      <td><span class="status ${paymentStatusClass(b.payment?.status)}">${mapPaymentStatus(b.payment?.status)}</span></td>
      <td>${Number(b.finalPrice || 0).toLocaleString("vi-VN")} đ</td>
      <td>
        <a class="detail-link" href="#" onclick="showBookingDetail('${b.bookingId}')">${bookingViewText}</a>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function showBookingDetail(bookingId) {
  try {
    const res = await fetch(`/api/bookings/${bookingId}`);
    if (!res.ok) throw new Error("Không thể tải chi tiết đặt sân");

    const data = await res.json();
    const historyRow = currentBookings.find((b) => b.bookingId === bookingId);
    const payment = historyRow?.payment || null;

    document.getElementById("modalPitchName").innerText = data.pitchName || "-";
    document.getElementById("modalBranchName").innerText = data.branchName || "-";
    document.getElementById("modalUserName").innerText = data.userName || "-";
    document.getElementById("modalBookingDate").innerText = data.bookingDate || "-";
    document.getElementById("modalStatus").innerText = mapStatus(data.status) || "-";
    document.getElementById("modalNote").innerText = data.note || "-";
    document.getElementById("modalPaymentStatus").innerText = mapPaymentStatus(payment?.status);
    document.getElementById("modalTxnRef").innerText = payment?.txnRef || "-";
    document.getElementById("modalVnpNo").innerText = payment?.vnpTransactionNo || "-";
    document.getElementById("modalBankCode").innerText = payment?.bankCode || "-";
    document.getElementById("modalPayDate").innerText = formatVnpPayDate(payment?.payDate);

    const slotsList = document.getElementById("modalSlotsList");
    slotsList.innerHTML = "";
    (data.slots || []).forEach(slot => {
      const li = document.createElement("li");
      li.textContent = `${formatDate(slot.startAt)} - ${formatDate(slot.endAt)} ${slot.checkedIn ? "(đã check-in)" : ""}`;
      slotsList.appendChild(li);
    });

    document.getElementById("bookingModal").style.display = "flex";
  } catch (e) {
    alert(e.message);
  }
}

function closeModal() {
  document.getElementById("bookingModal").style.display = "none";
}

function renderSummary() {
  const from = totalElements === 0 ? 0 : currentPage * pageSize + 1;
  const to = Math.min((currentPage + 1) * pageSize, totalElements);

  document.getElementById("summaryText").textContent =
    paginationRangeText
      .replace("{0}", from)
      .replace("{1}", to)
      .replace("{2}", totalElements);
}

function renderPagination(total, current) {
  const el = document.getElementById("pagination");
  el.innerHTML = "";
  if (total <= 1) return;

  let html = `<button class="page-btn" ${current === 0 ? "disabled" : ""} onclick="loadBookingHistory(${current - 1})">«</button>`;
  const windowSize = 7;
  let start = Math.max(0, current - Math.floor(windowSize / 2));
  let end = Math.min(total - 1, start + windowSize - 1);
  if (end - start + 1 < windowSize) start = Math.max(0, end - windowSize + 1);

  for (let i = start; i <= end; i++) {
    html += `<button class="page-btn ${i === current ? "active" : ""}" onclick="loadBookingHistory(${i})">${i + 1}</button>`;
  }

  html += `<button class="page-btn" ${current === total - 1 ? "disabled" : ""} onclick="loadBookingHistory(${current + 1})">»</button>`;
  el.innerHTML = html;
}

function changePageSize(val) {
  pageSize = parseInt(val, 10) || 10;
  loadBookingHistory(0);
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}

function formatVnpPayDate(value) {
  if (!value || value.length !== 14) return value || "-";
  return `${value.slice(6, 8)}/${value.slice(4, 6)}/${value.slice(0, 4)} ${value.slice(8, 10)}:${value.slice(10, 12)}:${value.slice(12, 14)}`;
}

function mapStatus(status) {
  if (!status) return "-";
  return statusTextMap[status] || status;
}

function mapPaymentStatus(status) {
  if (!status) return "-";
  return paymentStatusTextMap[status] || status;
}

function statusClass(status) {
  return status ? String(status).toLowerCase().replaceAll("_", "-") : "none";
}

function paymentStatusClass(status) {
  return status ? String(status).toLowerCase().replaceAll("_", "-") : "none";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

window.loadBookingHistory = loadBookingHistory;
window.showBookingDetail = showBookingDetail;
window.closeModal = closeModal;
window.changePageSize = changePageSize;
