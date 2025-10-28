const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const headers = options.headers || {};
  const token = localStorage.getItem("access_token");
  if (token) headers["Authorization"] = `Bearer ${token}`;
  headers["Content-Type"] = headers["Content-Type"] || "application/json";
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null } catch(e){ data = text; }
  if (!res.ok) {
    const err = new Error(data?.detail || res.statusText || 'API error');
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export async function register(payload) {
  return request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
}
export async function login(payload) {
  return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}
export async function getMembers() {
  return request("/members", { method: "GET" });
}
export async function addMember(member) {
  return request("/members", { method: "POST", body: JSON.stringify(member) });
}
export async function updateMember(id, member) {
  return request(`/members/${id}`, { method: "PUT", body: JSON.stringify(member) });
}
export async function deleteMember(id) {
  return request(`/members/${id}`, { method: "DELETE" });
}
