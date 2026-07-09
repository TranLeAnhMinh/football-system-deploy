/* ============================================================
   0. STATE
============================================================ */
let currentPage = 0;
let pageSize = 10;
let currentFilters = {
  role: "",
  status: "",
  name: "",
  email: ""
};


/* ============================================================
   1. INIT LOAD
============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  loadUsers();
  setupFilters();
});


/* ============================================================
   2. LOAD USERS
============================================================ */
async function loadUsers() {
  const tableBody = document.getElementById("userTableBody");
  if (!tableBody) return;

  tableBody.innerHTML = `<tr><td colspan="7">${i18n.loading}</td></tr>`;

  const params = new URLSearchParams();
  params.append("page", currentPage);
  params.append("size", pageSize);

  if (currentFilters.role) params.append("role", currentFilters.role);
  if (currentFilters.status) params.append("status", currentFilters.status);
  if (currentFilters.name) params.append("name", currentFilters.name);
  if (currentFilters.email) params.append("email", currentFilters.email);

  try {
    const res = await fetch(`/api/adminsystem/users?${params.toString()}`, {
      headers: {}
    });

    if (!res.ok) {
      tableBody.innerHTML = `<tr><td colspan="7">${i18n.error}</td></tr>`;
      return;
    }

    const data = await res.json();
    renderUsersTable(data.content);
    renderPagination(data);

  } catch (err) {
    console.error(err);
    tableBody.innerHTML = `<tr><td colspan="7">${i18n.error}</td></tr>`;
  }
}


/* ============================================================
   3. RENDER TABLE
============================================================ */
function renderUsersTable(users) {
  const tableBody = document.getElementById("userTableBody");
  if (!users || users.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-row">${i18n.empty}</td></tr>`;
    return;
  }

  tableBody.innerHTML = users.map(u => {
    return `
      <tr>
        <td>${u.fullName}</td>
        <td>${u.email}</td>
        <td>${u.phone ?? "-"}</td>

        <td>
          <span class="role-tag">${u.role}</span>
        </td>

        <td>
          <span class="status-tag ${u.status === "ACTIVE" ? "active" : "inactive"}">
            ${u.status}
          </span>
        </td>

        <td>${u.branchName ?? "-"}</td>

        <td class="action-cell">
          ${renderActionButtons(u)}
        </td>
      </tr>
    `;
  }).join("");
}


/* ============================================================
   3.1 ACTION BUTTON UI
============================================================ */
function renderActionButtons(user) {
  let btns = "";

  // Toggle ACTIVE/INACTIVE
  btns += `
    <button class="btn-small ${user.status === "ACTIVE" ? "btn-inactive" : "btn-active"}"
      onclick="toggleUserStatus('${user.id}', '${user.role}', '${user.status}')">
      ${user.status === "ACTIVE" ? i18n.deactivate : i18n.activate}
    </button>
  `;

  if (user.role === "ADMIN_BRANCH") {
    btns += `
      <button class="btn-small btn-delete"
        onclick="deleteAdminBranch('${user.id}')">
        ${i18n.deleteAdminBranch}
      </button>
    `;
  }

  // Approve pending admin branch
  if (user.role === "PENDING_ADMIN_BRANCH") {
    btns += `
      <button class="btn-small btn-approve"
        onclick="openApproveModal('${user.id}')">
        ${i18n.approve}
      </button>
    `;
  }

  return btns;
}


/* ============================================================
   4. PAGINATION
============================================================ */
function renderPagination(page) {
  const container = document.getElementById("paginationContainer");
  if (!container) return;

  container.innerHTML = "";

  for (let i = 0; i < page.totalPages; i++) {
    container.innerHTML += `
      <button class="page-btn ${i === page.number ? "active" : ""}"
        onclick="goPage(${i})">
        ${i + 1}
      </button>
    `;
  }
}

function goPage(p) {
  currentPage = p;
  loadUsers();
}


/* ============================================================
   5. FILTER HANDLING
============================================================ */
function setupFilters() {
  document.getElementById("filterRole")?.addEventListener("change", e => {
    currentFilters.role = e.target.value;
    currentPage = 0;
    loadUsers();
  });

  document.getElementById("filterStatus")?.addEventListener("change", e => {
    currentFilters.status = e.target.value;
    currentPage = 0;
    loadUsers();
  });

  document.getElementById("filterName")?.addEventListener("input", debounce(e => {
    currentFilters.name = e.target.value;
    currentPage = 0;
    loadUsers();
  }, 350));

  document.getElementById("filterEmail")?.addEventListener("input", debounce(e => {
    currentFilters.email = e.target.value;
    currentPage = 0;
    loadUsers();
  }, 350));
}


/* debounce helper */
function debounce(fn, delay) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), delay);
  };
}


/* ============================================================
   6. TOGGLE STATUS
============================================================ */
async function toggleUserStatus(userId, role, status) {
  if (role === "ADMIN_SYSTEM" && status === "ACTIVE") {
    alert(i18n.cannotDeactivateAdminSystem);
    return;
  }
const res = await fetch(`/api/adminsystem/users/${userId}/toggle-status`, {
    method: "PATCH",
    headers: {}
  });

  if (!res.ok) return alert(i18n.error);

  loadUsers();
}

async function deleteAdminBranch(userId) {
if (!confirm(i18n.confirmDeleteAdminBranch)) return;

  const res = await fetch(`/api/adminsystem/users/${userId}/admin-branch`, {
    method: "DELETE",
    headers: {}
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => null);
    alert(errData?.message || i18n.error);
    return;
  }

  loadUsers();
}

/* ============================================================
   7. APPROVE (CUSTOM MODAL)
============================================================ */
const approveModal = document.getElementById("approveModal");
const btnConfirm = document.getElementById("confirmApproveBtn");
const btnCancel  = document.getElementById("btnCloseApprove");

function openApproveModal(userId) {
  document.getElementById("approveUserId").value = userId;
  approveModal.classList.add("active");
  loadAvailableBranches(); 
}

function closeApproveModal() {
  approveModal.classList.remove("active");
}

btnCancel?.addEventListener("click", closeApproveModal);

btnConfirm?.addEventListener("click", async () => {
const userId = document.getElementById("approveUserId").value;
  const branchId = document.getElementById("approveBranchId").value;

  const res = await fetch(`/api/adminsystem/users/${userId}/approve-branch/${branchId}`, {
    method: "PATCH",
    headers: {}
  });

  if (!res.ok) return alert(i18n.error);

  closeApproveModal();
  loadUsers();
});

async function loadAvailableBranches() {
const dropdown = document.getElementById("approveBranchId");

  // clear old options
  dropdown.innerHTML = `<option value="">Đang tải...</option>`;

  try {
    const res = await fetch(`/api/adminsystem/users/branches/available`, {
      headers: {}
    });

    if (!res.ok) {
      dropdown.innerHTML = `<option value="">Lỗi tải dữ liệu</option>`;
      return;
    }

    const data = await res.json();

    if (!data || data.length === 0) {
      dropdown.innerHTML = `<option value="">Không còn chi nhánh trống</option>`;
      return;
    }

    // Set options
    dropdown.innerHTML = data.map(b =>
      `<option value="${b.id}">${b.name}</option>`
    ).join("");

  } catch (err) {
    dropdown.innerHTML = `<option value="">Lỗi server</option>`;
  }
}




