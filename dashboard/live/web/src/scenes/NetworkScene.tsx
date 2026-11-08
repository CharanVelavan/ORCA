import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Html, Line, OrbitControls, useGLTF } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import * as THREE from 'three';
import { useLiveStore } from '../store';
import { useUi } from '../stage/uiStore';
import type { SiteState } from '../types';
import { usePipeline } from '../pipeline/pipelineStore';
import { shotFor, DEFAULT_OFFSET, type Effect } from './beats3d';
import { EffectsLayer, useFxDescriptor } from './effects/EffectsLayer';
import { attackerHome, GATEWAYS, MGMT, SAT, SITES, type Palette } from './geo';
import './scene.css';

// Stage/Console 3D network (plan section 10). Emulated Chennai: 6 sites, 3 gateways, one GEO satellite.
// No bloom; colours come from the CSS tokens at runtime. Beat-driven effects live in ./effects (see beats3d.ts).

const readPalette = (): Palette => {
  const cs = getComputedStyle(document.documentElement);
  const v = (n: string, f: string) => cs.getPropertyValue(n).trim() || f;
  return { bg: v('--bg', '#111316'), surface: v('--surface', '#1A1D21'), surface2: v('--surface-2', '#22262B'), ink: v('--ink', '#E7E9EC'), muted: v('--ink-muted', '#9AA3AE'), border: v('--border', '#2A2E34'), accent: v('--accent', '#7FA7CF'), ok: v('--ok', '#74B08C'), warn: v('--warn', '#D6A24E'), critical: v('--critical', '#E07F72'), healing: v('--healing', '#A39BDA'), unknown: v('--unknown', '#8A8F98') };
};
const stateColor = (p: Palette, s?: string) => s === 'down' ? p.critical : s === 'degraded' ? p.warn : s === 'healing' ? p.healing : s === 'ok' ? p.ok : p.unknown;

function Model({ name, palette, scale = 1, opacity = 1, ...rest }: { name: string; palette: Palette; scale?: number; opacity?: number } & JSX.IntrinsicElements['group']) {
  const { scene } = useGLTF('./models/orca-assets.glb');
  const obj = useMemo(() => {
    const src = scene.getObjectByName(name);
    if (!src) return null;
    const c = src.clone(true);
    c.position.set(0, 0, 0);
    c.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const old = m.material as THREE.MeshStandardMaterial;
      const key = old.name;
      const color = key === 'panel' ? palette.accent : key === 'accent' ? palette.warn : key === 'dark' ? palette.surface : palette.muted;
      m.material = new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0, transparent: opacity < 1, opacity });
    });
    return c;
  }, [scene, name, palette, opacity]);
  if (!obj) return null;
  return <group {...rest} scale={scale}><primitive object={obj} /></group>;
}

function Ground({ palette }: { palette: Palette }) {
  // Chennai tile with a stylised coastline on the east (Bay of Bengal).
  const coast = useMemo(() => [[2.2, 0.01, -4.5], [2.0, 0.01, -3.0], [2.3, 0.01, -1.4], [2.1, 0.01, 0.2], [2.4, 0.01, 1.6], [2.3, 0.01, 3.2], [2.6, 0.01, 4.5]] as [number, number, number][], []);
  return (
    <group>
      <mesh rotation-x={-Math.PI / 2} position={[-1.5, -0.01, 0]}><planeGeometry args={[9, 10]} /><meshStandardMaterial color={palette.surface} roughness={1} /></mesh>
      <mesh rotation-x={-Math.PI / 2} position={[5.0, -0.02, 0]}><planeGeometry args={[5, 10]} /><meshStandardMaterial color={palette.bg} roughness={1} /></mesh>
      <gridHelper args={[14, 28, palette.border, palette.border]} position={[0, 0.001, 0]} />
      <Line points={coast} color={palette.accent} lineWidth={1.2} transparent opacity={0.55} />
    </group>
  );
}

function Satellite({ palette }: { palette: Palette }) {
  const g = useRef<THREE.Group>(null);
  const reduced = useReducedMotionFlag();
  useFrame(({ clock }) => { if (g.current && !reduced) g.current.rotation.y = Math.sin(clock.elapsedTime * 0.15) * 0.25; });
  const arc = useMemo(() => new THREE.EllipseCurve(0, 0, 9, 9, Math.PI * 0.15, Math.PI * 0.85).getPoints(48).map((p) => [p.x - 0.6, 5.2 + (p.y - 9 * Math.sin(Math.PI / 2)) * 0.25, -0.4] as [number, number, number]), []);
  return (
    <group>
      <Line points={arc} color={palette.border} lineWidth={1} dashed dashSize={0.2} gapSize={0.15} />
      <group ref={g} position={SAT}><Model name="Satellite" palette={palette} scale={1.3} /></group>
      <Html position={[SAT[0], SAT[1] + 0.9, SAT[2]]} center><span className="scn-label scn-label--sat">GEO satellite · emulated</span></Html>
    </group>
  );
}

function Links({ palette, sites, paths }: { palette: Palette; sites: Record<string, SiteState>; paths: Record<string, unknown>[] }) {
  return (
    <group>
      {Object.entries(SITES).map(([id, s]) => {
        const st = sites[id];
        const active = paths.find((p) => p.site === id && p.active) as { path?: string; gateway?: string; kind?: string } | undefined;
        const gw = (active?.gateway ?? st?.gateway ?? 'GW-IN-1') as string;
        const g = GATEWAYS[gw] ?? GATEWAYS['GW-IN-1'];
        const color = stateColor(palette, st?.state);
        const satPath = !active?.path || active.path === 'A' || gw.startsWith('GW');
        const top: [number, number, number] = [s.pos[0], 0.95, s.pos[2]];
        return (
          <group key={id}>
            {satPath
              ? <Line points={[top, SAT]} color={color} lineWidth={st?.state === 'down' ? 1 : 1.6} transparent opacity={st?.state === 'down' ? 0.35 : 0.85} dashed={st?.state === 'down'} dashSize={0.18} gapSize={0.14} />
              : null}
            {active && active.path !== 'A' && <Line points={[top, [(top[0] + g.pos[0]) / 2, 1.6, (top[2] + g.pos[2]) / 2], [g.pos[0], 0.9, g.pos[2]]]} color={palette.healing} lineWidth={2} />}
          </group>
        );
      })}
      {Object.entries(GATEWAYS).filter(([, g]) => !g.foreign).map(([id, g]) => <Line key={id} points={[[g.pos[0], 1.0, g.pos[2]], SAT]} color={palette.accent} lineWidth={1} transparent opacity={0.45} />)}
    </group>
  );
}

function Sites({ palette, sites, focus }: { palette: Palette; sites: Record<string, SiteState>; focus: string | null }) {
  return (
    <group>
      {Object.entries(SITES).map(([id, s]) => {
        const st = sites[id];
        const color = stateColor(palette, st?.state);
        return (
          <group key={id} position={s.pos}>
            <mesh rotation-x={-Math.PI / 2} position-y={0.005}><ringGeometry args={[0.32, 0.4, 40]} /><meshBasicMaterial color={color} transparent opacity={0.9} /></mesh>
            <Model name="CellTower" palette={palette} scale={0.95} />
            <Model name="UserTerminal" palette={palette} scale={0.32} position={[0.45, 0, 0.25]} />
            <Html position={[0, 1.25, 0]} center>
              <span className={`scn-label ${focus === id ? 'is-focus' : ''}`} data-state={st?.state ?? 'unknown'}><span className="scn-dot" />{s.name}{st?.state && st.state !== 'ok' ? <b>{st.state.toUpperCase()}</b> : null}</span>
            </Html>
          </group>
        );
      })}
    </group>
  );
}

function Gateways({ palette, gateways }: { palette: Palette; gateways: Record<string, string> }) {
  return (
    <group>
      {Object.entries(GATEWAYS).map(([id, g]) => (
        <group key={id} position={g.pos}>
          <Model name="GatewayDish" palette={palette} scale={1.1} opacity={g.foreign ? 0.35 : 1} />
          <Html position={[0, 1.4, 0]} center>
            <span className="scn-label" data-state={g.foreign ? 'locked' : gateways[id] === 'down' ? 'down' : 'ok'}><span className="scn-dot" />{g.name}<b>{g.foreign ? 'NOT ALLOWED' : (gateways[id] ?? 'up').toUpperCase()}</b></span>
          </Html>
        </group>
      ))}
    </group>
  );
}

function Attacker({ palette, target, injector }: { palette: Palette; target: string | null; injector: string }) {
  const m = useRef<THREE.Mesh>(null);
  const g = useRef<THREE.Group>(null);
  const born = useRef<number | null>(null);
  const reduced = useReducedMotionFlag();
  useEffect(() => { born.current = null; }, [target, injector]);
  useFrame(({ clock }) => {
    if (m.current && !reduced) { m.current.rotation.y = clock.elapsedTime; m.current.position.y = 2.2 + Math.sin(clock.elapsedTime * 2) * 0.08; }
    if (g.current) { // the threat node rises in
      born.current ??= clock.elapsedTime;
      g.current.scale.setScalar(reduced ? 1 : Math.min(1, (clock.elapsedTime - born.current) / 0.6));
    }
  });
  if (!target) return null;
  const pos = attackerHome(injector, target);
  return (
    <group ref={g} position={pos}>
      <mesh ref={m} position-y={2.2}><octahedronGeometry args={[0.22]} /><meshStandardMaterial color={palette.critical} roughness={0.6} /></mesh>
      <Line points={[[0, 2.2, 0], [0, 0.05, 0]]} color={palette.critical} lineWidth={1.2} dashed dashSize={0.12} gapSize={0.1} />
      <Html position={[0, 2.85, 0]} center><span className="scn-label scn-label--threat">Threat source · director view</span></Html>
    </group>
  );
}

/** SAT-MGMT: the satellite operator's management network, a small server block beside GW-IN-1. */
function Mgmt({ palette }: { palette: Palette }) {
  const g = GATEWAYS['GW-IN-1'].pos;
  return (
    <group>
      <group position={MGMT}>
        <mesh position-y={0.3}><boxGeometry args={[0.6, 0.6, 0.42]} /><meshStandardMaterial color={palette.surface2} roughness={0.9} /></mesh>
        <mesh position-y={0.62}><boxGeometry args={[0.6, 0.05, 0.42]} /><meshStandardMaterial color={palette.accent} roughness={0.8} /></mesh>
        <Html position={[0, 0.95, 0]} center><span className="scn-label scn-label--mgmt"><span className="scn-dot" />SAT-MGMT</span></Html>
      </group>
      <Line points={[[MGMT[0], 0.6, MGMT[2]], [g[0], 0.9, g[2]]]} color={palette.border} lineWidth={1} dashed dashSize={0.12} gapSize={0.1} />
    </group>
  );
}

/**
 * Camera: scripted shot per effect kind (threat close-up, agent cluster, commander wide, heal follow), eased with a
 * critically damped exponential. Dragging pauses the auto-follow for 8 s. Without a beat, follows the site in trouble.
 */
function CameraRig({ focus, fx }: { focus: string | null; fx: Effect }) {
  const { camera } = useThree();
  const controls = useThree((s) => s.controls) as OrbitControlsImpl | null;
  const target = useRef(new THREE.Vector3(0, 1.2, 0));
  const want = useRef(new THREE.Vector3(0, 1.2, 0));
  const wantOff = useRef(new THREE.Vector3(...DEFAULT_OFFSET));
  const pausedUntil = useRef(0);
  const reduced = useReducedMotionFlag();
  const nodes = useRef(usePipeline.getState().nodes);
  useEffect(() => usePipeline.subscribe((s) => { nodes.current = s.nodes; }), []);
  useEffect(() => {
    const shot = shotFor(fx, nodes.current);
    if (shot) { want.current.set(...shot.target); wantOff.current.set(...shot.offset); return; }
    const p = focus ? SITES[focus]?.pos ?? GATEWAYS[focus]?.pos : null;
    want.current.set(p ? p[0] * 0.5 : 0, 1.2, p ? p[2] * 0.5 : 0);
    wantOff.current.set(...DEFAULT_OFFSET);
  }, [focus, fx]);
  useEffect(() => {
    if (!controls) return;
    const pause = () => { pausedUntil.current = performance.now() + 8000; };
    controls.addEventListener('start', pause);
    controls.addEventListener('end', pause);
    return () => { controls.removeEventListener('start', pause); controls.removeEventListener('end', pause); };
  }, [controls]);
  const goal = useMemo(() => new THREE.Vector3(), []);
  useFrame((_, dt) => {
    if (performance.now() < pausedUntil.current) { controls?.update(); return; }
    const k = reduced ? 1 : 1 - Math.exp(-Math.min(dt, 0.1) * 3.2); // about 1.2 s per shot, no bounce
    target.current.lerp(want.current, k);
    goal.copy(target.current).add(wantOff.current);
    camera.position.lerp(goal, k);
    if (controls) { controls.target.copy(target.current); controls.update(); } else camera.lookAt(target.current);
  });
  return null;
}

function useReducedMotionFlag() {
  const [r, setR] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => { const mq = window.matchMedia('(prefers-reduced-motion: reduce)'); const f = () => setR(mq.matches); mq.addEventListener('change', f); return () => mq.removeEventListener('change', f); }, []);
  return r;
}

export function NetworkScene({ truth }: { truth: boolean }) {
  const theme = useUi((s) => s.theme);
  const [palette, setPalette] = useState<Palette>(readPalette);
  useEffect(() => { const id = requestAnimationFrame(() => setPalette(readPalette())); return () => cancelAnimationFrame(id); }, [theme]);
  const sites = useLiveStore((s) => s.sites);
  const gateways = useLiveStore((s) => s.gateways);
  const paths = useLiveStore((s) => s.paths);
  const truthEvents = useLiveStore((s) => s.truth);
  const [focus, setFocus] = useState<string | null>(null);
  const prev = useRef<Record<string, string>>({});
  useEffect(() => {
    for (const [id, st] of Object.entries(sites)) {
      if (prev.current[id] && prev.current[id] !== st.state) setFocus(st.state === 'ok' ? null : id);
      prev.current[id] = st.state;
    }
  }, [sites]);
  // Attacker marker: ground truth only (Stage, Control, Review). Never on the Console.
  const lastInject = truth ? truthEvents.filter((e) => e.kind === 'inject').slice(-1)[0] : undefined;
  const injTarget = lastInject ? String(lastInject.target ?? '') : null;
  const attackTarget = injTarget && (SITES[injTarget] || GATEWAYS[injTarget]) ? injTarget : injTarget ? 'CHN-01' : null;
  const isAttack = lastInject && String(lastInject.truth_class ?? '').startsWith('attack');
  const injector = lastInject ? String(lastInject.injector ?? '') : '';
  const fx = useFxDescriptor();
  const reduced = useReducedMotionFlag();

  return (
    <div className="scn" data-theme-key={theme}>
      <Canvas dpr={[1, 2]} camera={{ position: [7.5, 7.2, 6.5], fov: 38 }} gl={{ antialias: true, powerPreference: 'high-performance' }}>
        <color attach="background" args={[palette.bg]} />
        <fog attach="fog" args={[palette.bg, 16, 30]} />
        <hemisphereLight args={[palette.ink, palette.bg, 0.9]} />
        <directionalLight position={[4, 8, 3]} intensity={1.1} />
        <Suspense fallback={null}>
          <Ground palette={palette} />
          <Links palette={palette} sites={sites} paths={paths} />
          <Sites palette={palette} sites={sites} focus={focus} />
          <Gateways palette={palette} gateways={gateways} />
          <Satellite palette={palette} />
          {truth && isAttack && <Attacker palette={palette} target={attackTarget} injector={injector} />}
          <Mgmt palette={palette} />
          <EffectsLayer fx={fx} palette={palette} truth={truth} reduced={reduced} />
        </Suspense>
        <OrbitControls makeDefault enablePan={false} enableZoom={false} enableDamping dampingFactor={0.12} maxPolarAngle={Math.PI / 2.15} minPolarAngle={0.35} />
        <CameraRig focus={focus} fx={fx} />
      </Canvas>
      <div className="scn-tag mono">EMULATED NETWORK · CHENNAI</div>
      <div className="scn-legend">
        <span data-state="ok"><i />OK</span><span data-state="degraded"><i />Degraded</span><span data-state="down"><i />Down</span><span data-state="healing"><i />Healing</span>
      </div>
    </div>
  );
}

useGLTF.preload('./models/orca-assets.glb');
