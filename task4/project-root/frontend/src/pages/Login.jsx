import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api";

export default function Login() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState(null);
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setErr(null);
    try {
      const data = await login({ identifier, password });
      // data: { access_token, token_type }
      localStorage.setItem("access_token", data.access_token);
      nav("/welcome");
    } catch (e) {
      setErr(e.data?.detail || e.message);
    }
  }

  return (
    <div style={{ maxWidth: 360 }}>
      <h3>Login</h3>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <form onSubmit={submit}>
        <div>
          <label>Username or Email</label><br/>
          <input value={identifier} onChange={e=>setIdentifier(e.target.value)} required/>
        </div>
        <div style={{ marginTop: 8 }}>
          <label>Password</label><br/>
          <input value={password} onChange={e=>setPassword(e.target.value)} type="password" required/>
        </div>
        <button style={{ marginTop: 10 }} type="submit">Login</button>
      </form>
    </div>
  );
}
