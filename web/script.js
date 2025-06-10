async function signUrl() {
  const url = document.getElementById("url").value;
  const res = await fetch("/sign", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  const data = await res.json();
  document.getElementById("output").innerText = JSON.stringify(data, null, 2);
}

async function verifyUrl() {
  const url = document.getElementById("url").value;
  const res = await fetch("/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  const data = await res.json();
  document.getElementById("output").innerText = JSON.stringify(data, null, 2);
}
