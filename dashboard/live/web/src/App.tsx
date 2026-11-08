import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { DataBridge } from './stage/DataBridge';
import { useUi } from './stage/uiStore';

const Landing = lazy(() => import('./Landing').then((m) => ({ default: m.Landing })));
const Stage = lazy(() => import('./Stage').then((m) => ({ default: m.Stage })));
const Console = lazy(() => import('./Console').then((m) => ({ default: m.Console })));
const Control = lazy(() => import('./Control').then((m) => ({ default: m.Control })));
const Review = lazy(() => import('./Review').then((m) => ({ default: m.Review })));

function ThemeSync() {
  const theme = useUi((s) => s.theme);
  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
  return null;
}

function Loading() {
  return <main className="app-loading"><span className="mono">ORCA-NTN</span><span>Loading view</span></main>;
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeSync />
      <DataBridge />
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/stage" element={<Stage />} />
          <Route path="/console" element={<Console />} />
          <Route path="/control" element={<Control />} />
          <Route path="/review" element={<Review />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
