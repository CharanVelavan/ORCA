import { ArrowRight, BookOpen, Download, ShieldCheck } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { PageFrame } from '../PageFrame';
import './guide.css';

const scenarios = [
  ['S0', 'Normal operation', 'Establish a baseline for telemetry and rules.'],
  ['S1', 'Ground-management intrusion', 'Trace stolen credentials, terminal loss and guarded recovery.'],
  ['S2', 'Rain and capacity', 'Compare forecasts, battery risk and service allocation.'],
  ['S3', 'Jamming and backup trust', 'Inspect path integrity and domestic gateway checks.'],
  ['N1', 'Battery cliff', 'Follow a power fault at the hospital corridor.'],
  ['N2', 'Payment routing fault', 'Inspect the routing change and downstream warning.'],
  ['N3', 'Unprotected feeder link', 'Review configuration evidence and M3 abstention.'],
  ['N4', 'False dashboard health', 'Compare management reports with independent service evidence.'],
  ['N5', 'Multiple reporting clocks', 'Inspect grid impact, triggers and cited duties.'],
  ['CAP', 'Combined crisis', 'Separate concurrent weather, intrusion and capacity evidence.'],
];
const files = [
  ['Dashboard guide', 'The full guide to controls and the judge walkthrough.', '/docs/guide.md'],
  ['Reproducibility guide', 'Setup, hardware planning, model and vector-index options.', '/docs/JUDGE_REPRODUCIBILITY.md'],
  ['Windows quick start', 'Windows launcher, optional downloads and platform limits.', '/docs/JUDGE_WINDOWS.md'],
];

export default function Guide() {
  const { search } = useLocation();
  return <PageFrame title="Guide" subtitle="Run an exercise and follow the evidence">
    <div className="guide-page">
      <div className="guide-intro"><span className="guide-kicker"><BookOpen size={15} /> ORCA—NTN / FIELD GUIDE</span><h2>From first launch<br />to a defensible finding.</h2><p>Explore the emulated Chennai network, start a scenario and inspect what the sandbox actually records. Every satellite, gateway and link is emulated.</p><div className="guide-intro__actions"><Link className="guide-button" to={`/scenarios${search}`}>Choose a scenario <ArrowRight size={16}/></Link><a href="#guide-downloads">Download the guides <Download size={16}/></a></div></div>
      <nav className="guide-jump" aria-label="Guide sections"><a href="#guide-start">01 &nbsp; Start</a><a href="#guide-exercises">02 &nbsp; Scenarios</a><a href="#guide-modes">03 &nbsp; Run modes</a><a href="#guide-evidence">04 &nbsp; Evidence</a><a href="#guide-downloads">05 &nbsp; Downloads</a></nav>
      <section className="guide-section" id="guide-start" aria-labelledby="guide-start-title"><div className="guide-heading"><span>01 / QUICK START</span><h2 id="guide-start-title">Start locally.</h2><p>From the repository root, with 64-bit Python 3.12 installed:</p></div><div><div className="guide-commands"><div><span>macOS / Linux</span><code>./quickstart.sh</code></div><div><span>Windows PowerShell / Command Prompt</span><code>.\quickstart.bat</code></div></div><p>Open <code>http://127.0.0.1:8060/</code>. The first setup installs dependencies and may train the network-model cache; allow several minutes. The server starts paused. Choose a scenario and press <strong>Start exercise</strong> to start it.</p><p>Mock mode needs neither a model server nor the optional vector index. First installation requires network access. Native Windows launch has been statically reviewed but not executed on Windows.</p></div></section>
      <section className="guide-section" id="guide-exercises" aria-labelledby="guide-exercises-title"><div className="guide-heading"><span>02 / SCENARIOS</span><h2 id="guide-exercises-title">Choose an exercise.</h2><p>Selecting a card previews the script. Starting it creates the active run.</p><Link className="guide-text-link" to={`/scenarios${search}`}>Open scenarios <ArrowRight size={15}/></Link></div><div className="guide-scenarios">{scenarios.map(([id,title,description]) => <article key={id}><b>{id}</b><div><h3>{title}</h3><p>{description}</p></div></article>)}</div></section>
      <section className="guide-section" id="guide-modes" aria-labelledby="guide-modes-title"><div className="guide-heading"><span>03 / SOURCE MODES</span><h2 id="guide-modes-title">Know what is running.</h2></div><div className="guide-modes"><article><h3>Mock simulation</h3><p>A fresh simulator run with M1–M4, deterministic rules and scripted agent stand-ins. It makes no Qwen request; guarded controls can change the emulated network.</p></article><article><h3>Live endpoint / Qwen</h3><p>A fresh run whose agents call a configured compatible model endpoint. Test the endpoint and select its exact advertised model ID before starting.</p></article><article><h3>Recorded replay</h3><p>Previously recorded events, with no new inference or network change. Replay remains read-only across views; return to live in Audit before changing the exercise.</p></article><p className="guide-note">Dashboard replay is different from <code>LLM_MODE=replay</code>, which requires matching model-call cache files. A chat server, embedding endpoint and vector index are separate optional components.</p></div></section>
      <section className="guide-section" id="guide-evidence" aria-labelledby="guide-evidence-title"><div className="guide-heading"><span>04 / EVIDENCE</span><h2 id="guide-evidence-title">Follow the record.</h2><p>Planned scenario events are not proof that an action happened.</p></div><ol className="guide-steps"><li><strong>Console</strong><span>Inspect released telemetry, model outputs, agents and the exact approval request. Director truth is separately labeled.</span></li><li><strong>Policy &amp; Gaps</strong><span>Read cited records, independent reporting triggers and candidate findings. Indian rules govern new exercises; global material is comparative.</span></li><li><strong>Recovery</strong><span>Inspect actual approvals, route checks, stage health, re-attack results and refusals. Missing evidence remains missing.</span></li><li><strong>Audit &amp; Replay</strong><span>Select a recording, inspect the events and verify its original chain. A recording evidence export can contain multiple incidents and cannot verify that original chain by itself.</span></li></ol></section>
      <section className="guide-downloads" id="guide-downloads" aria-labelledby="guide-downloads-title"><div><span className="guide-kicker"><ShieldCheck size={15}/> OFFLINE DOCUMENTS</span><h2 id="guide-downloads-title">Keep the full guides.</h2><p>These Markdown files are copied from the repository at build time. Links inside them use repository-relative paths.</p></div><div className="guide-files">{files.map(([title,description,href]) => <a href={href} download key={href}><div><strong>{title}</strong><span>{description}</span></div><Download size={18}/></a>)}</div></section>
    </div>
  </PageFrame>;
}
