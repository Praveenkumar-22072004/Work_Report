import React, {useState, useEffect} from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function Header(){ 
  return (
    <header className='p-6 flex items-center justify-between'>
      <div className='header-logo'>
        <svg height='40' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'><path fill='#0ea5e9' d='M3 10.5c0-1.1.9-2 2-2h1l1-2h8l1 2h1c1.1 0 2 .9 2 2v3h-18v-3z'/></svg>
        <div>
          <div className='text-xl brand-accent'>CarTasks</div>
          <div className='text-xs text-gray-400'>Group To-Dos with style</div>
        </div>
      </div>
      <div>
        <button className='button-car' id='new-group-btn'>+ New Group</button>
      </div>
    </header>
  )
}

function GroupCard({g, onInvite, onCreateTask}){
  const [inviteEmail, setInviteEmail] = useState('')
  const [taskTitle, setTaskTitle] = useState('')
  const [assignee, setAssignee] = useState('')
  return (
    <div className='card my-4 p-4'>
      <h3 className='text-lg font-bold'>{g.name}</h3>
      <p className='text-sm text-gray-300'>{g.description}</p>
      <div className='mt-3 flex gap-2'>
        <input placeholder='email to invite' value={inviteEmail} onChange={e=>setInviteEmail(e.target.value)} className='p-2 rounded bg-black/20' />
        <button className='button-car' onClick={()=>{ onInvite(g.id, inviteEmail); setInviteEmail('') }}>Invite</button>
      </div>
      <div className='mt-3 flex gap-2'>
        <input placeholder='task title' value={taskTitle} onChange={e=>setTaskTitle(e.target.value)} className='p-2 rounded bg-black/20' />
        <input placeholder='assignee email (optional)' value={assignee} onChange={e=>setAssignee(e.target.value)} className='p-2 rounded bg-black/20' />
        <button className='button-car' onClick={()=>{ onCreateTask(g.id, taskTitle, assignee); setTaskTitle(''); setAssignee('') }}>Create Task</button>
      </div>
    </div>
  )
}

export default function App(){
  const [groups, setGroups] = useState([])
  const [name, setName] = useState('')
  const [descr, setDescr] = useState('')

  useEffect(()=>{ fetchGroups() },[])

  async function fetchGroups(){
    try{
      const res = await axios.get(API + '/groups')  // we'll provide a simple stub in backend
      setGroups(res.data.groups || [])
    }catch(e){
      console.log('failed to fetch groups', e)
    }
  }

  async function createGroup(){
    if(!name) return alert('enter name')
    await axios.post(API + '/groups/', { name, description: descr })
    setName(''); setDescr(''); fetchGroups()
  }

  async function invite(groupId, email){
    if(!email) return alert('enter email')
    await axios.post(`${API}/groups/${groupId}/invite`, { email })
    alert('Invitation sent (or attempted).')
  }

  async function createTask(groupId, title, assignee_email){
    if(!title) return alert('enter title')
    await axios.post(`${API}/groups/${groupId}/tasks`, { title, description: '', assignee_email })
    alert('Task created (and email sent if assigned).')
  }

  return (
    <div className='min-h-screen p-6'>
      <Header />
      <main className='max-w-4xl mx-auto'>
        <div className='card p-6'>
          <h2 className='text-2xl font-bold'>Create Group</h2>
          <div className='mt-3 flex gap-2'>
            <input value={name} onChange={e=>setName(e.target.value)} placeholder='Group name' className='p-2 rounded bg-black/20'/>
            <input value={descr} onChange={e=>setDescr(e.target.value)} placeholder='Description' className='p-2 rounded bg-black/20'/>
            <button className='button-car' onClick={createGroup}>Create</button>
          </div>
        </div>

        <div className='mt-6'>
          {groups.map(g=> <GroupCard key={g.id} g={g} onInvite={invite} onCreateTask={createTask} />)}
        </div>
      </main>
    </div>
  )
}
