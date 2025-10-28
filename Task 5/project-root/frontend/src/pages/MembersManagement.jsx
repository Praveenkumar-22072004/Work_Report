import React, { useEffect, useState } from "react";
import { getMembers, addMember, updateMember, deleteMember } from "../api";

export default function MembersManagement() {
  const [members, setMembers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    organization: "",
  });
  const [err, setErr] = useState(null);

  async function load() {
    try {
      const data = await getMembers();
      setMembers(data);
    } catch (e) {
      setErr(e.data?.detail || e.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function submit(e) {
    e.preventDefault();
    try {
      if (editing) {
        await updateMember(editing.id, form);
        setEditing(null);
      } else {
        await addMember(form);
      }
      setForm({ name: "", email: "", phone: "", organization: "" });
      load();
    } catch (e) {
      setErr(e.data?.detail || e.message);
    }
  }

  function startEdit(m) {
    setEditing(m);
    setForm({
      name: m.name,
      email: m.email,
      phone: m.phone,
      organization: m.organization,
    });
  }

  async function doDelete(id) {
    if (!confirm("Delete member?")) return;
    await deleteMember(id);
    load();
  }

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-5xl bg-white p-6 rounded-2xl shadow-strong">
        <h3 className="text-2xl font-heading text-gray-900 mb-4">Members</h3>

        {err && (
          <div
            className="mb-4 rounded-md bg-red-100 p-2 text-sm text-red-700"
            role="alert"
          >
            {err}
          </div>
        )}

        {/* Form */}
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-2 mb-6">
          <input
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            className="input"
          />
          <input
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
            className="input"
          />
          <input
            placeholder="Phone"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="input"
          />
          <input
            placeholder="Organization"
            value={form.organization}
            onChange={(e) => setForm({ ...form, organization: e.target.value })}
            className="input"
          />

          <div className="flex items-center gap-2 md:col-span-2">
            <button type="submit" className="btn btn-primary">
              {editing ? "Update" : "Add"}
            </button>
            {editing && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setEditing(null);
                  setForm({ name: "", email: "", phone: "", organization: "" });
                }}
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        {/* Members Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  Name
                </th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  Email
                </th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  Phone
                </th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">
                  Organization
                </th>
                <th className="px-4 py-2 text-sm font-semibold text-gray-700 text-center">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr
                  key={m.id}
                  className="border-t hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-2">{m.name}</td>
                  <td className="px-4 py-2">{m.email}</td>
                  <td className="px-4 py-2">{m.phone}</td>
                  <td className="px-4 py-2">{m.organization}</td>
                  <td className="px-4 py-2 flex justify-center gap-2">
                    <button
                      onClick={() => startEdit(m)}
                      className="btn btn-secondary"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => doDelete(m.id)}
                      className="btn btn-danger"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {members.length === 0 && (
                <tr>
                  <td
                    colSpan="5"
                    className="px-4 py-4 text-center text-gray-500"
                  >
                    No members found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
