import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useEffect, useMemo, useState } from 'react';
import * as THREE from 'three';
import { useLiveStore } from '../store';
import type { LiveEvent, SiteState } from '../types';

type SceneProps = { showTruth?: boolean; replayEvents?: LiveEvent[] };
type Preset = 'city' | 'network' | 'satellite';
const spots: { id: string; position: [number, number, number]; dependants: string[] }[] = [
  { id: 'CHN-01', position: [-2, 0, 0], dependants: ['112', 'Hospital'] },
  { id: 'CHN-02', position: [0, 0, .25], dependants: ['UPI', 'Grid'] },
  { id: 'CHN-03', position: [2, 0, -.25], dependants: ['112', 'Hospital'] },
];
const cameras: Record<Preset, [number, number, number]> = { city: [0, 5.5, 7], network: [0, 8.2, 4.3], satellite: [0, 11, 1.2] };
const tone = (site: SiteState | undefined) => site?.state === 'down' ? '#B5473A' : site?.state === 'healing' ? '#5E57A0' : site?.state === 'degraded' ? '#A86F12' : '#3F7D58';

export function NetworkScene({ showTruth = false, replayEvents }: SceneProps) {
  const liveSites = useLiveStore(s => s.sites); const livePaths = useLiveStore(s => s.paths);
  const [webgl, setWebgl] = useState(true); const [preset, setPreset] = useState<Preset>('city'); const [selected, setSelected] = useState<string | null>(null);
  const reduced = useMemo(() => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false, []);
  const snapshot = useMemo(() => { const tick = [...(replayEvents ?? [])].reverse().find(e => e.kind === 'tick'); return { sites: (tick?.sites as Record<string, SiteState> | undefined) ?? liveSites, paths: (tick?.paths as Record<string, unknown>[] | undefined) ?? livePaths }; }, [livePaths, liveSites, replayEvents]);
  const truth = useMemo(() => showTruth ? (replayEvents ?? useLiveStore.getState().truth).filter(e => e.kind === 'inject') : [], [replayEvents, showTruth]);
  useEffect(() => { const onKey = (event: KeyboardEvent) => { if (event.key === '1') setPreset('city'); if (event.key === '2') setPreset('network'); if (event.key === '3') setPreset('satellite'); }; window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey); }, []);
  if (!webgl || reduced) return <NetworkFallback sites={snapshot.sites} selected={selected} onSelect={setSelected} />;
  return <div className="network-scene">
    <div className="scene-presets" role="group" aria-label="Camera presets">{(['city', 'network', 'satellite'] as Preset[]).map((item, index) => <button key={item} className={preset === item ? 'is-active' : ''} onClick={() => setPreset(item)}>{item[0].toUpperCase() + item.slice(1)} <kbd>{index + 1}</kbd></button>)}</div>
    <Canvas dpr={[1, 2]} camera={{ position: cameras.city, fov: 44 }} onCreated={({ gl }) => { if (!gl.capabilities.isWebGL2) setWebgl(false); }}>
      <color attach="background" args={['#e9e6df']} /><ambientLight intensity={1.3} /><directionalLight position={[4, 6, 4]} intensity={1.6} />
      <CameraRig preset={preset} reduced={reduced} /><Ground />{spots.map(site => <Tower key={site.id} {...site} state={snapshot.sites[site.id]} selected={selected} onSelect={setSelected} />)}
      <Gateway id="GW-IN-1" position={[-3, 0, -1.7]} /><Gateway id="GW-IN-2" position={[3, 0, -1.7]} /><Gateway id="GW-XX" position={[4, 0, 2]} foreign />
      {spots.map(site => <LinkPath key={site.id} from={site.position} active={String(snapshot.sites[site.id]?.gateway) === 'GW-IN-2'} selected={selected === site.id} color={tone(snapshot.sites[site.id])} />)}
      <Satellite />{truth.map(event => <AttackVisual key={`${event.id}-${event.seq}`} event={event} />)}<SceneControls />
    </Canvas><div className="scene-label">Stylised Chennai · links are emulated</div>
  </div>;
}
function CameraRig({ preset, reduced }: { preset: Preset; reduced: boolean }) { const { camera, invalidate } = useThree(); const target = useMemo(() => new THREE.Vector3(), []); useEffect(() => { target.fromArray(cameras[preset]); if (reduced) { camera.position.copy(target); invalidate(); } }, [camera, invalidate, preset, reduced, target]); useFrame((_, delta) => { if (!reduced) { camera.position.lerp(target, 1 - Math.exp(-delta / .7)); camera.lookAt(0, 0, 0); } }); return null; }
function SceneControls() { const { camera, gl } = useThree(); useEffect(() => { let active = false, x = 0; const down = (event: PointerEvent) => { active = true; x = event.clientX; }; const move = (event: PointerEvent) => { if (!active) return; const angle = (event.clientX - x) * .006; camera.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), angle); camera.lookAt(0, 0, 0); x = event.clientX; }; const up = () => { active = false; }; gl.domElement.addEventListener('pointerdown', down); window.addEventListener('pointermove', move); window.addEventListener('pointerup', up); return () => { gl.domElement.removeEventListener('pointerdown', down); window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); }; }, [camera, gl]); return null; }
function Ground() { return <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow><planeGeometry args={[11, 8]} /><meshStandardMaterial color="#dedbd3" roughness={.95} /></mesh>; }
function Tower({ id, position, state, selected, onSelect }: { id: string; position: [number, number, number]; dependants: string[]; state: SiteState | undefined; selected: string | null; onSelect: (id: string | null) => void }) { const c = tone(state); const dimmed = selected !== null && selected !== id; return <group position={position} scale={dimmed ? .75 : 1}><mesh position={[0, .45, 0]} onClick={() => onSelect(selected === id ? null : id)}><cylinderGeometry args={[.13, .19, .9, 12]} /><meshStandardMaterial color={c} roughness={.7} /></mesh>{selected === id && <SceneLine points={[[0, .15, 0], [-3, 0, -1.7]]} color="#2F5D8A" />}</group>; }
function Gateway({ position, foreign = false }: { id: string; position: [number, number, number]; foreign?: boolean }) { return <group position={position}><mesh position={[0, .18, 0]}><boxGeometry args={[.48, .36, .48]} /><meshStandardMaterial color={foreign ? '#A86F12' : '#2F5D8A'} roughness={.65} /></mesh></group>; }
function Satellite() { return <group position={[0, 3.2, -.5]}><mesh><sphereGeometry args={[.22, 16, 16]} /><meshStandardMaterial color="#7c8996" roughness={.5} /></mesh><SceneLine points={[[-3, 0, 0], [0, .1, 0], [3, 0, 0]]} color="#7c8996" /></group>; }
function SceneLine({ points, color }: { points: number[][]; color: string }) { const positions = useMemo(() => new Float32Array(points.flat()), [points]); return <line><bufferGeometry><bufferAttribute attach="attributes-position" args={[positions, 3]} /></bufferGeometry><lineBasicMaterial color={color} transparent opacity={.7} /></line>; }
function LinkPath({ from, color, active, selected }: { from: [number, number, number]; color: string; active: boolean; selected: boolean }) { return <SceneLine points={[from, [0, 3.1, -.5]]} color={selected ? '#2F5D8A' : active ? color : '#8A8F98'} />; }
function AttackVisual({ event }: { event: LiveEvent }) { const kind = String(event.injector ?? event.id ?? ''); const target = spots.find(s => s.id === event.target)?.position ?? spots[1].position; if (kind.includes('rain')) return <mesh position={[target[0], 1, target[2]]}><sphereGeometry args={[.8, 16, 12]} /><meshStandardMaterial color="#7193b7" transparent opacity={.28} /></mesh>; if (kind.includes('power')) return <mesh position={[target[0], .5, target[2]]} rotation={[-Math.PI / 2, 0, 0]}><torusGeometry args={[.38, .04, 8, 24]} /><meshStandardMaterial color="#A86F12" /></mesh>; return <group position={[target[0], .7, target[2]]}><mesh><torusGeometry args={[kind.includes('jamming') ? .55 : .22, .04, 8, 24]} /><meshStandardMaterial color="#B5473A" /></mesh><SceneLine points={[[target[0], .7, target[2]], [0, 3.15, -.5]]} color="#B5473A" /></group>; }
function NetworkFallback({ sites, selected, onSelect }: { sites: Record<string, SiteState>; selected: string | null; onSelect: (id: string | null) => void }) { return <div className="network-fallback" aria-label="Network map fallback"><svg viewBox="0 0 800 300" role="img"><path className="coast" d="M80 250 Q280 50 560 130 T750 220" />{spots.map((s, i) => <g key={s.id} opacity={selected && selected !== s.id ? .45 : 1} onClick={() => onSelect(selected === s.id ? null : s.id)}><line x1={400} y1={42} x2={170 + i * 220} y2={185} stroke={tone(sites[s.id])} strokeDasharray="7 5" /><circle cx={170 + i * 220} cy={185} r={15} fill={tone(sites[s.id])} /><text x={145 + i * 220} y={218}>{s.id}</text></g>)}<circle cx={400} cy={42} r={15} fill="#7c8996" /><text x={360} y={20}>Satellite (emulated)</text></svg><div className="scene-label">Flat map fallback · links are emulated</div></div>; }
