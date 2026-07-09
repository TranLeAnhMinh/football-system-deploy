document.addEventListener("DOMContentLoaded", () => {
  const icon = document.getElementById("chatbot-icon");
  const chatWindow = document.getElementById("chatbot-window");
  const closeBtn = document.getElementById("chatbot-close");
  const input = document.getElementById("chatbot-input");
  const sendBtn = document.getElementById("chatbot-send");
  const messages = document.getElementById("chatbot-messages");
  const suggestions = document.getElementById("chatbot-suggestions");

  if (!icon || !chatWindow || !closeBtn || !input || !sendBtn || !messages) return;

  // const RASA_URL = "http://localhost:5005/webhooks/rest/webhook";
  const RASA_URL = "/rasa/webhooks/rest/webhook";
  const senderId = "web_user_" + Date.now();

  function getCurrentLanguage() {
    const params = new URLSearchParams(window.location.search);
    const lang = params.get("lang");

    if (lang === "vi") return "vi";
    if (lang === "en") return "en";
    if (lang === "ja") return "ja";

    return "vi";
  }

  function getTypingText() {
    const lang = getCurrentLanguage();
    if (lang === "en") return "Replying...";
    if (lang === "ja") return "回答中...";
    return "Đang trả lời...";
  }

  function getFallbackText() {
    const lang = getCurrentLanguage();
    if (lang === "en") return "I don't have a suitable answer yet.";
    if (lang === "ja") return "適切な回答がまだありません。";
    return "Tôi chưa có câu trả lời phù hợp.";
  }

  function getConnectionErrorText() {
    const lang = getCurrentLanguage();
    if (lang === "en") return "❌ Cannot connect to the Rasa chatbot.";
    if (lang === "ja") return "❌ Rasaチャットボットに接続できません。";
    return "❌ Không thể kết nối tới Rasa chatbot.";
  }

  function hideSuggestions() {
    if (suggestions) {
      suggestions.style.display = "none";
    }
  }

  icon.addEventListener("click", () => {
    chatWindow.classList.toggle("hidden");
  });

  closeBtn.addEventListener("click", () => {
    chatWindow.classList.add("hidden");
  });

  let isDragging = false;
  let offsetX = 0;
  let offsetY = 0;

  icon.addEventListener("mousedown", (e) => {
    isDragging = true;
    offsetX = e.clientX - icon.getBoundingClientRect().left;
    offsetY = e.clientY - icon.getBoundingClientRect().top;
    icon.style.cursor = "grabbing";
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    icon.style.left = e.clientX - offsetX + "px";
    icon.style.top = e.clientY - offsetY + "px";
    icon.style.bottom = "auto";
    icon.style.right = "auto";
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    icon.style.cursor = "grab";
  });

  function addMessage(text, type) {
    const msg = document.createElement("div");
    msg.className = `msg ${type}`;
    msg.innerText = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage(predefinedQuestion = null) {
    const question = predefinedQuestion || input.value.trim();
    if (!question) return;

    hideSuggestions();

    const language = getCurrentLanguage();

    addMessage(question, "user");

    if (!predefinedQuestion) {
      input.value = "";
    } else {
      input.value = "";
    }

    const typing = document.createElement("div");
    typing.className = "msg bot";
    typing.innerText = getTypingText();
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch(RASA_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          sender: senderId,
          message: question,
          metadata: {
            language: language
          }
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP error: ${res.status}`);
      }

      const data = await res.json();
      typing.remove();

      if (!Array.isArray(data) || data.length === 0) {
        addMessage(getFallbackText(), "bot");
        return;
      }

      data.forEach((item) => {
        if (item.text) addMessage(item.text, "bot");
      });
    } catch (err) {
      typing.remove();
      addMessage(getConnectionErrorText(), "bot");
      console.error("Chatbot error:", err);
    }
  }

  document.querySelectorAll(".suggestion-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const question = btn.innerText.trim();
      sendMessage(question);
    });
  });

  sendBtn.addEventListener("click", () => sendMessage());

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
});



