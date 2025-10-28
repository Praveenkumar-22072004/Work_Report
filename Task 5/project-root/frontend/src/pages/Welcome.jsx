import React from "react";
import { Link, useNavigate } from "react-router-dom";

export default function Welcome() {
  const nav = useNavigate();
  function logout() {
    localStorage.removeItem("access_token");
    nav("/login");
  }
  return (
    <div>
      <h2>Welcome</h2>
      <p>This page is shown after login.</p>
      <Link to="/members">Manage members</Link>
      <div style={{ marginTop: 12 }}>
        <button onClick={logout}>Logout</button>
      </div>
    </div>
  );
}
    