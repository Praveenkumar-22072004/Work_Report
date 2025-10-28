import React, { useState } from "react";
import { register } from "../api";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [err, setErr] = useState(null);
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setErr(null);
    if (password !== confirm) {
      setErr("Passwords do not match");
      return;
    }
    try {
      await register({ username, email, password });
      nav("/login");
    } catch (e) {
      setErr(e.data?.detail || e.message);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-strong p-6">
        <h3 className="text-2xl font-heading text-gray-900 mb-4">
          Create Account
        </h3>

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
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="mt-1 block w-full rounded-md border-gray-300 shadow-soft focus:border-primary focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              className="mt-1 block w-full rounded-md border-gray-300 shadow-soft focus:border-primary focus:ring-primary"
            />
          </div>

          <button
            type="submit"
            disabled={!username || !email || !password}
            className="btn btn-primary w-full disabled:opacity-50"
          >
            Create Account
          </button>
        </form>
      </div>
    </div>
  );
}
