import React, { useEffect, useState } from "react";
import { getMembers, addMember, updateMember, deleteMember } from "../api";

export default function MembersManagement() {
  const [members, setMembers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", email: "", phone: "", organization: "" });
  const [err, setErr] = useState(null);

  async function load() {
    try {
      const data = await getMembers();
      setMembers(data);
    } catch (e) {
      setErr(e.data?.detail || e.message);
    }
  }

  useEffect(()=>{ load(); }, []);

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

  async function startEdit(m) {
    setEditing(m);
    setForm({ name: m.name, email: m.email, phone: m.phone, organization: m.organization });
  }

  async function doDelete(id) {
    if (!confirm("Delete member?")) return;
    await deleteMember(id);
    load();
  }

  return (
    <div style={{ maxWidth: 900 }}>
      <h3>Members</h3>
      {err && <div style={{ color: "crimson" }}>{err}</div>}

      <form onSubmit={submit} style={{ marginBottom: 12 }}>
        <input placeholder="Name" value={form.name} onChange={e=>setForm({...form, name: e.target.value})} required/>
        <input placeholder="Email" value={form.email} onChange={e=>setForm({...form, email: e.target.value})} required/>
        <input placeholder="Phone" value={form.phone} onChange={e=>setForm({...form, phone: e.target.value})}/>
        <input placeholder="Organization" value={form.organization} onChange={e=>setForm({...form, organization: e.target.value})}/>
        <button type="submit">{editing ? "Update" : "Add"}</button>
        {editing && <button type="button" onClick={()=>{ setEditing(null); setForm({ name: "", email: "", phone: "", organization: "" })}}>Cancel</button>}
      </form>

      <table border="1" cellPadding="8" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th>Name</th><th>Email</th><th>Phone</th><th>Organization</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {members.map(m => (
            <tr key={m.id}>
              <td>{m.name}</td>
              <td>{m.email}</td>
              <td>{m.phone}</td>
              <td>{m.organization}</td>
              <td>
                <button onClick={()=>startEdit(m)}>Edit</button>
                <button onClick={()=>doDelete(m.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
