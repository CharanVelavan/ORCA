import { useEffect } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Shell } from './components/Shell';
import { playFake } from './fake/play';
import { connectStream } from './stream';
import { useLiveStore } from './store';
import { Console } from './Console';

function Placeholder({title}:{title:string}) { return <Shell><main className="placeholder"><p className="eyebrow">ORCA Live</p><h1>{title}</h1><p>This route uses the shared live session shell. Its exercise controls are being prepared alongside the operator console.</p></main></Shell>; }
function DataBridge() { const add=useLiveStore(s=>s.add); const reset=useLiveStore(s=>s.reset); useEffect(()=>{ reset(); const fake=new URLSearchParams(location.search).get('fake')==='1'; return fake?playFake(add):connectStream(0,add); },[add,reset]); return null; }
export default function App() { return <BrowserRouter><DataBridge/><Routes><Route path="/" element={<Placeholder title="ORCA-NTN"/>}/><Route path="/console" element={<Console/>}/><Route path="/control" element={<Placeholder title="Exercise Control"/>}/><Route path="/review" element={<Placeholder title="After-action review"/>}/></Routes></BrowserRouter>; }
