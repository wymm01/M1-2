// ---- 탭 전환 ----
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");

    if (btn.dataset.tab === "data") loadDataList();
    if (btn.dataset.tab === "history") loadConversationList();
  });
});

// ---- 요약 정보 로드 ----
async function loadSummary() {
  const box = document.getElementById("summary-box");
  try {
    const res = await fetch(`${API_BASE_URL}/api/data/summary`);
    const s = await res.json();
    if (!s.count) {
      box.textContent = "아직 저장된 데이터가 없습니다.";
      return;
    }
    box.textContent =
      `기간: ${s.period.start} ~ ${s.period.end} | 개수: ${s.count} | ` +
      `평균: ${s.average} | 최고: ${s.max} | 최저: ${s.min} | 추세: ${s.recent_trend}`;
  } catch (e) {
    box.textContent = "요약 정보를 불러오지 못했습니다. (서버 콜드스타트 중일 수 있어요, 잠시 후 새로고침 해주세요)";
  }
}

// ---- 채팅 ----
let currentConversationId = null;

function appendMessage(role, content) {
  const wrap = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `<span class="bubble"></span>`;
  div.querySelector(".bubble").textContent = content;
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  appendMessage("user", message);
  input.value = "";
  document.getElementById("chat-loading").classList.remove("hidden");

  try {
    const res = await fetch(`${API_BASE_URL}/api/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        conversation_id: currentConversationId,
      }),
    });
    if (!res.ok) throw new Error("서버 응답 오류");
    const data = await res.json();
    currentConversationId = data.conversation_id;
    appendMessage("assistant", data.reply);
    loadSummary(); // 요약이 바뀌었을 수도 있으니 갱신
  } catch (err) {
    appendMessage("assistant", "⚠️ 답변을 가져오지 못했습니다. 서버가 콜드스타트 중이면 30초~1분 후 다시 시도해주세요.");
  } finally {
    document.getElementById("chat-loading").classList.add("hidden");
  }
});

// ---- 초기 로드 ----
loadSummary();
// ---- 데이터 관리 탭 ----
async function loadDataList() {
  const tbody = document.querySelector("#data-table tbody");
  tbody.innerHTML = "<tr><td colspan='4'>불러오는 중...</td></tr>";
  try {
    const res = await fetch(`${API_BASE_URL}/api/data/`);
    const data = await res.json();
    tbody.innerHTML = "";
    data.data.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.date}</td>
        <td>${item.value}</td>
        <td>${item.memo ?? ""}</td>
        <td><button data-id="${item.id}">삭제</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = "<tr><td colspan='4'>목록을 불러오지 못했습니다.</td></tr>";
  }
}

document.getElementById("data-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const date = document.getElementById("data-date").value;
  const value = parseFloat(document.getElementById("data-value").value);
  const memo = document.getElementById("data-memo").value;

  try {
    const res = await fetch(`${API_BASE_URL}/api/data/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date, value, memo: memo || null }),
    });
    if (!res.ok) throw new Error("추가 실패");
    document.getElementById("data-form").reset();
    loadDataList();
    loadSummary();
  } catch (err) {
    alert("데이터 추가에 실패했습니다.");
  }
});

// 삭제 버튼 클릭 (이벤트 위임)
document.querySelector("#data-table tbody")?.addEventListener("click", async (e) => {
  if (e.target.tagName !== "BUTTON") return;
  const id = e.target.dataset.id;
  if (!confirm("이 데이터를 삭제할까요?")) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/data/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("삭제 실패");
    loadDataList();
    loadSummary();
  } catch (err) {
    alert("삭제에 실패했습니다.");
  }
});

// ---- 대화 기록 탭 ----
async function loadConversationList() {
  const list = document.getElementById("conversation-list");
  list.innerHTML = "<li>불러오는 중...</li>";
  try {
    const res = await fetch(`${API_BASE_URL}/api/conversations/`);
    const data = await res.json();
    list.innerHTML = "";
    if (data.count === 0) {
      list.innerHTML = "<li>저장된 대화가 없습니다.</li>";
      return;
    }
    data.conversations.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = `${c.title || "(제목 없음)"} · 메시지 ${c.message_count}개`;
      li.addEventListener("click", () => loadConversationDetail(c.id));
      list.appendChild(li);
    });
  } catch (e) {
    list.innerHTML = "<li>대화 목록을 불러오지 못했습니다.</li>";
  }
}

async function loadConversationDetail(id) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/conversations/${id}`);
    const data = await res.json();

    // 채팅 탭으로 전환하고 메시지 재표시
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    document.querySelector('[data-tab="chat"]').classList.add("active");
    document.getElementById("chat").classList.add("active");

    const wrap = document.getElementById("chat-messages");
    wrap.innerHTML = "";
    data.messages.forEach((m) => appendMessage(m.role, m.content));

    currentConversationId = data.id; // 이 대화에 이어서 채팅 가능
  } catch (e) {
    alert("대화를 불러오지 못했습니다.");
  }
}