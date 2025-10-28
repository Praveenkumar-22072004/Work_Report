import React, { useState } from "react";
import { register } from "../api";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [username,setUsername] = useState("");
  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");
  const [confirm,setConfirm] = useState("");
  const [err,setErr] = useState(null);
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setErr(null);
    if (password !== confirm) { setErr("Passwords do not match"); return; }
    try {
      await register({ username, email, password });
      nav("/login");
    } catch (e) {
      setErr(e.data?.detail || e.message);
    }
  }

  return (
    <div style={{ maxWidth: 420 }}>
      <h3>Register</h3>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <form onSubmit={submit}>
        <div>
          <label>Username</label><br/>
          <input value={username} onChange={e=>setUsername(e.target.value)} required/>
        </div>
        <div>
          <label>Email</label><br/>
          <input value={email} onChange={e=>setEmail(e.target.value)} type="email" required/>
        </div>
        <div>
          <label>Password</label><br/>
          <input value={password} onChange={e=>setPassword(e.target.value)} type="password" required/>
        </div>
        <div>
          <label>Confirm password</label><br/>
          <input value={confirm} onChange={e=>setConfirm(e.target.value)} type="password" required/>
        </div>
        <button style={{ marginTop: 8 }} type="submit" disabled={!username || !email || !password}>Create account</button>
      </form>
    </div>
  );
}
