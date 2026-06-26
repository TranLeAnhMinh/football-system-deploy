document.addEventListener("DOMContentLoaded", async () => {
  const pitchId = window.PITCH_ID;
  const token = localStorage.getItem("accessToken");

  let calendar;
  let isRefreshing = false;
  let refreshInterval = null;

  function showToast(msg, type = "success") {
    const box = document.createElement("div");
    box.className = `toast ${type}`;
    box.textContent = msg;
    document.getElementById("toast-container").appendChild(box);
    setTimeout(() => box.remove(), 3500);
  }

  if (!pitchId || !token) {
    showToast("⚠️ Thiếu thông tin xác thực hoặc sân!", "error");
    return;
  }

  const authHeaders = { Authorization: "Bearer " + token };
  const calendarEl = document.getElementById("calendar");

  /* ---------- Helper ---------- */
  const formatDate = (str) =>
    new Date(str).toLocaleString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      day: "2-digit",
      month: "2-digit",
    });

  function toOffsetDateTimeLocal(datetime) {
    if (!datetime) return "";

    const date = new Date(datetime);
    const tzOffsetMin = -date.getTimezoneOffset();
    const sign = tzOffsetMin >= 0 ? "+" : "-";
    const absOffset = Math.abs(tzOffsetMin);
    const hoursOffset = String(Math.floor(absOffset / 60)).padStart(2, "0");
    const minutesOffset = String(absOffset % 60).padStart(2, "0");

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    const second = String(date.getSeconds()).padStart(2, "0");

    return `${year}-${month}-${day}T${hour}:${minute}:${second}${sign}${hoursOffset}:${minutesOffset}`;
  }

  function convertToLocal(isoString) {
    if (!isoString) return isoString;

    const date = new Date(isoString);

    return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 19);
  }

  /* ---------- Load Events ---------- */
  async function loadEvents() {
    try {
      const now = new Date();
      const from = new Date(
        now.getFullYear(),
        now.getMonth(),
        1
      ).toISOString();

      const to = new Date(
        now.getFullYear(),
        now.getMonth() + 1,
        0,
        23,
        59,
        59
      ).toISOString();

      const [mwRes, slotRes] = await Promise.all([
        fetch(`/api/pitches/${pitchId}/maintenance-windows?from=${from}&to=${to}`, {
          headers: authHeaders,
        }),
        fetch(`/api/pitches/${pitchId}/booking-slots?from=${from}&to=${to}`, {
          headers: authHeaders,
        }),
      ]);

      if (!mwRes.ok || !slotRes.ok) {
        throw new Error("Load calendar events failed");
      }

      const mws = await mwRes.json();
      const slots = await slotRes.json();

      calendar.removeAllEvents();

      // 🟥 Maintenance
      mws.forEach((m) => {
        calendar.addEvent({
          id: m.id,
          title: m.reason || window.i18n.maintenance,
          start: convertToLocal(m.startAt),
          end: convertToLocal(m.endAt),
          backgroundColor: "#ef4444",
          borderColor: "#dc2626",
          textColor: "#ffffff",
          description: `${window.i18n.maintenance}: ${m.reason || ""}`,
        });
      });

      // 🟨 PENDING / 🟩 APPROVED
      slots.forEach((s) => {
        const isPending = s.status === "PENDING";

        calendar.addEvent({
          id: s.id,
          title: isPending
            ? "Đang giữ chỗ"
            : s.userFullName || "Đã đặt",

          start: convertToLocal(s.startAt),
          end: convertToLocal(s.endAt),

          backgroundColor: isPending ? "#facc15" : "#10b981",
          borderColor: isPending ? "#eab308" : "#059669",
          textColor: isPending ? "#000000" : "#ffffff",

          description: isPending
            ? `Đang giữ chỗ: ${formatDate(s.startAt)} → ${formatDate(s.endAt)}`
            : `Booking: ${formatDate(s.startAt)} → ${formatDate(s.endAt)}`,

          extendedProps: {
            status: s.status,
          },
        });
      });
    } catch (err) {
      console.error("❌ Lỗi load events:", err);
      showToast(window.i18n.error, "error");
    }
  }

  async function refreshEventsSafely() {
    if (isRefreshing) return;

    isRefreshing = true;

    try {
      await loadEvents();
    } catch (err) {
      console.error("Refresh calendar failed:", err);
    } finally {
      isRefreshing = false;
    }
  }

  /* ---------- FullCalendar ---------- */
  calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    timeZone: "local",
    locale: document.documentElement.lang || "vi",
    height: 700,
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    eventTimeFormat: {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    },
    eventDidMount(info) {
      if (info.event.extendedProps.description) {
        new bootstrap.Tooltip(info.el, {
          title: info.event.extendedProps.description,
          placement: "top",
          trigger: "hover",
          container: "body",
        });
      }

      info.el.style.opacity = "0";
      setTimeout(() => {
        info.el.style.opacity = "1";
      }, 50);
    },
  });

  calendar.render();

  // Load lần đầu an toàn
  await refreshEventsSafely();

  // Nếu đã có interval cũ thì xóa
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }

  // Refresh mỗi 30 giây
  refreshInterval = setInterval(refreshEventsSafely, 30000);

  /* ---------- Submit Form ---------- */
  const form = document.getElementById("maintenanceForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const startInput = document.getElementById("startDate").value;
    const endInput = document.getElementById("endDate").value;
    const reason = document.getElementById("reason").value.trim();

    if (!startInput || !endInput || !reason) {
      showToast("⚠️ Vui lòng nhập đầy đủ thông tin!", "error");
      return;
    }

    const startAt = toOffsetDateTimeLocal(startInput);
    const endAt = toOffsetDateTimeLocal(endInput);

    try {
      const overlapRes = await fetch(
        `/api/pitches/${pitchId}/maintenance-windows/check-overlap?` +
          new URLSearchParams({ startAt, endAt }),
        { headers: authHeaders }
      );

      if (!overlapRes.ok) {
        throw new Error("Check overlap failed");
      }

      const overlapData = await overlapRes.json();

      if (overlapData.conflict && overlapData.overlaps.length > 0) {
        const list = overlapData.overlaps
          .map(
            (o) =>
              `• ${o.userName} (${formatDate(o.startAt)} → ${formatDate(o.endAt)})`
          )
          .join("\n");

        if (!confirm(`${window.i18n.confirmOverlap}\n\n${list}`)) {
          return;
        }
      }

      const res = await fetch(`/api/pitches/${pitchId}/maintenance-windows`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          pitchId,
          startAt,
          endAt,
          reason,
        }),
      });

      if (!res.ok) {
        let msg = "❌ Đã xảy ra lỗi, vui lòng thử lại!";

        try {
          const errText = await res.text();
          console.error("❌ Server response:", errText);

          const errBody = JSON.parse(errText);
          msg = errBody.message || msg;
        } catch {
          if (res.status === 409) {
            msg = "⚠️ Khung giờ bảo trì bị trùng!";
          }
        }

        showToast(msg, "error");
        alert(msg);
        return;
      }

      bootstrap.Modal.getInstance(
        document.getElementById("maintenanceModal")
      ).hide();

      showToast("✅ " + window.i18n.success, "success");

      await refreshEventsSafely();
    } catch (err) {
      console.error("❌ Lỗi khi tạo maintenance:", err);
      showToast("❌ " + window.i18n.error, "error");
      alert("❌ " + window.i18n.error);
    }
  });
});