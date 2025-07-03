async function signUrl() {
  const url = document.getElementById("url").value;
  const res = await fetch("/sign", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  const data = await res.json();
  renderOutput(data);
}

async function verifyUrl() {
  const url = document.getElementById("url").value;
  const res = await fetch("/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  const data = await res.json();
  renderOutput(data);
}

function renderOutput(data) {
  if (data.error) {
    document.getElementById("output").innerHTML =
      `<div style="color:#f44336;font-weight:bold;text-transform:uppercase;text-align:center;">${data.error}</div>`;
    return;
  }
  let html = "";
  if (data.status === "signed") {
    html += `<div><b>✅ Đã gắn chữ ký thành công!</b></div>`;
    html += `<div><b>Hash:</b> <code>${data.hash}</code></div>`;
  } else if (typeof data["KIỂM TRA"] !== "undefined") {
    html += `<div><b>Kết quả kiểm tra:</b> <span style="color:${data["KIỂM TRA"] ? '#4caf50' : '#f44336'};font-weight:bold;">${data["KẾT QUẢ"]}</span></div>`;
    html += `<div><b>Hash hiện tại:</b> <code>${data["HASH HIỆN TẠI"] || "-"}</code></div>`;
    html += `<div><b>Hash ban đầu:</b> <code>${data["HASH BAN ĐẦU"] || "-"}</code></div>`;
    if (data.nft_info && Object.keys(data.nft_info).length > 0) {
      html += `<div style="margin-top:8px;"><b>Thông tin NFT:</b><ul style="margin:4px 0 0 18px;padding:0;">`;
      for (const [k, v] of Object.entries(data.nft_info)) {
        html += `<li><b>${k}:</b> ${v}</li>`;
      }
      html += `</ul></div>`;
    }
  } else {
    html = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  }
  document.getElementById("output").innerHTML = html;
}

async function loadHistory() {
  const res = await fetch("/history", { credentials: "include" });
  const data = await res.json();
  const list = document.getElementById("history-list");
  list.innerHTML = "";
  data.urls.forEach(url => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = url;
    a.textContent = url;
    a.target = "_blank";
    a.style.color = "#fff";
    a.style.textDecoration = "underline";
    li.appendChild(a);
    list.appendChild(li);
  });
}

function toggleHistory() {
  const historyDiv = document.getElementById("history");
  if (historyDiv.style.display === "none") {
    loadHistory();
    historyDiv.style.display = "block";
  } else {
    historyDiv.style.display = "none";
  }
}

// Hiển thị modal
function showLogin() { document.getElementById('login-modal').style.display = 'block'; }
function showRegister() { document.getElementById('register-modal').style.display = 'block'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// Đăng ký
async function register() {
  const username = document.getElementById('register-username').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;
  const res = await fetch('/register', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({username, email, password})
  });
  const data = await res.json();
  document.getElementById('register-msg').innerText = data.status === 'ok' ? 'Đăng ký thành công! Đang chuyển hướng...' : data.msg;
  if(data.status === 'ok') {
    setTimeout(() => {
      window.location.href = "login.html";
    }, 1200);
  }
}

// Đăng nhập
async function login() {
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  const res = await fetch('/login', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({username, password}),
    credentials: "include"
  });
  const data = await res.json();
  document.getElementById('login-msg').innerText = data.status === 'ok' ? 'Đăng nhập thành công! Đang chuyển hướng...' : data.msg;
  if(data.status === 'ok') {
    // Kiểm tra quyền admin
    const me = await fetch('/me', { credentials: "include" });
    if (me.status === 200) {
      const user = await me.json();
      if (user.is_admin) {
        window.location.href = "admin.html";
        return;
      }
    }
    window.location.href = "index.html";
  }
}

// Đăng xuất
async function logout() {
  await fetch('/logout');
  updateAuthUI(null);
}

// Cập nhật giao diện đăng nhập/đăng xuất
function updateAuthUI(username) {
  document.getElementById('btn-login').style.display = username ? 'none' : '';
  document.getElementById('btn-register').style.display = username ? 'none' : '';
  document.getElementById('btn-logout').style.display = username ? '' : 'none';
  document.getElementById('welcome-user').style.display = username ? '' : 'none';
  document.getElementById('welcome-user').innerText = username ? `Xin chào, ${username}` : '';
}

function updateNavbarAuth(isLoggedIn) {
  const loginLink = document.getElementById('login-link');
  if (!loginLink) return;
  if (isLoggedIn) {
    loginLink.textContent = "Tài khoản";
    loginLink.href = "account.html";
    loginLink.onclick = null;
  } else {
    loginLink.textContent = "Đăng nhập";
    loginLink.href = "login.html";
    loginLink.onclick = null;
  }
}

// Kiểm tra trạng thái đăng nhập khi load trang (có thể dùng thêm API /me nếu muốn)
window.onload = function() {
  // Đơn giản: ẩn hết, chờ đăng nhập
  updateAuthUI(null);
}

// Gọi hàm này khi load trang để kiểm tra trạng thái đăng nhập
window.addEventListener("DOMContentLoaded", async () => {
  const loginLink = document.getElementById('login-link');
  if (!loginLink) return;
  let isLoggedIn = false;
  try {
    const res = await fetch('/me', { credentials: "include" });
    if (res.status === 200) isLoggedIn = true;
  } catch {}
  updateNavbarAuth(isLoggedIn);
});

function viewUserHistory(username) {
  fetch(`/admin/user_history/${encodeURIComponent(username)}`, { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      alert("Lịch sử URL của " + username + ":\n" + data.urls.join("\n"));
      // Bạn có thể thay alert bằng modal hoặc render ra bảng tùy ý
    });
}
