import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom';
import { playFake } from './fake/play';
import { connectStream } from './stream';
import { useLiveStore } from './store';
const Console = lazy(() => import('./Console').then(m => ({default:m.Console})));
const Control = lazy(() => import('./Control').then(m => ({default:m.Control})));
const Review = lazy(() => import('./Review').then(m => ({default:m.Review})));
const Landing = lazy(() => import('./Landing').then(m => ({default:m.Landing})));

function DataBridge() { const add=useLiveStore(s=>s.add); const addControl=useLiveStore(s=>s.addControl); const reset=useLiveStore(s=>s.reset); const location=useLocation(); useEffect(()=>{ reset(); const receiver=(location.pathname==='/control'||location.pathname==='/review')?addControl:add; const fake=new URLSearchParams(location.search).get('fake')==='1'; return fake?playFake(receiver):connectStream(0,receiver); },[add,addControl,location.pathname,location.search,reset]); return null; }
function Loading(){return <main className="placeholder"><p className="eyebrow">ORCA Live</p><h1>Loading view…</h1></main>}
export default function App() { return <BrowserRouter><DataBridge/><Suspense fallback={<Loading/>}><Routes><Route path="/" element={<Landing/>}/><Route path="/console" element={<Console/>}/><Route path="/control" element={<Control/>}/><Route path="/review" element={<Review/>}/></Routes></Suspense></BrowserRouter>; }
