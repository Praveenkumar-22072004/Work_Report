import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Welcome from "./pages/Welcome";
import MembersManagement from "./pages/MembersManagement";

export default function App() {
  return (
    <div style={{ padding: 20, fontFamily: 'Arial, sans-serif' }}>
      <nav style={{ marginBottom: 20 }}>
        <Link to="/" style={{ marginRight: 10 }}>Home</Link>
        <Link to="/login" style={{ marginRight: 10 }}>Login</Link>
        <Link to="/register" style={{ marginRight: 10 }}>Register</Link>
        <Link to="/welcome">Welcome</Link>
      </nav>

      <Routes>
        <Route path="/" element={<div><h1>Hello World</h1></div>} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/members" element={<MembersManagement />} />
      </Routes>
    </div>
  );
}
