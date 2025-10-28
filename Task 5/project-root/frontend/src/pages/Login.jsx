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
      localStorage.setItem("access_token", data.access_token);
      nav("/welcome");
    } catch (e) {
      setErr(e.data?.detail || e.message);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-strong p-6">
        <h3 className="text-2xl font-heading text-gray-900 mb-4">Login</h3>

        {err && (
          <div
            className="mb-4 rounded-md bg-red-100 p-2 text-sm text-red-700"
            role="alert"
          >
            {err}
          </div>
        )}

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Username or Email
            </label>
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              className="mt-1 block w-full rounded-md border-gray-300 shadow-soft focus:border-primary focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 block w-full rounded-md border-gray-300 shadow-soft focus:border-primary focus:ring-primary"
            />
          </div>

          <button type="submit" className="btn btn-primary w-full">
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
