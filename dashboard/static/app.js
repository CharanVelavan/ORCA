/* ORCA-NTN dashboard. Plain JS, no libraries, no network except this server. */
"use strict";

const VERDICTS = ["COMPLIANT", "VIOLATION", "AMBIGUITY", "CONFLICT", "POTENTIAL_GAP", "INSUFFICIENT_EVIDENCE"];
const TYPE_COLOR = {
  scenario_event: "#37474f", task: "#90a4ae", tool_call: "#1976d2", final: "#00897b", message: "#7b1fa2",
  message_rejected: "#c62828", approval: "#ef6c00", execution: "#2e7d32", autonomy: "#6d4c41", kill: "#c62828",
  gap: "#f9a825", verdict: "#1565c0", adviser: "#5e35b1", error: "#c62828", net: "#00838f", meta: "#9e9e9e", other: "#9e9e9e",
};
const TYPE_LABEL = {
  scenario_event: "event", task: "task", tool_call: "tool call", final: "answer", message: "message",
  message_rejected: "msg refused", approval: "approval", execution: "execution", autonomy: "autonomy", kill: "kill switch",
  gap: "gap", verdict: "verdict", adviser: "adviser", error: "error", net: "network", meta: "run info", other: "other",
};
const MILESTONE = new Set(["scenario_event", "approval", "execution", "kill", "autonomy", "gap", "message_rejected", "error"]);
const STATE = {
  normal: ["#eef6f0", "#7aa889", "normal"], at_risk: ["#fff4e0", "#e0a040", "forecast risk"],
  suspect: ["#fff8d6", "#d4b000", "suspect"], fault: ["#ffe9cc", "#e08a00", "fault"],
  attack: ["#ffd9d6", "#d32f2f", "under attack"], down: ["#f3c7c7", "#8e0000", "down"],
  contained: ["#e3eefc", "#3b7bd4", "contained"], healed: ["#d9f2e1", "#1b8a4a", "healed on backup"],
  protected: ["#dff3f1", "#13867b", "protected"],
};
const LANE_FIRST = ["scenario", "M1", "M2", "M3", "M4", "attacker", "environment"];
const LANE_LAST = ["commander", "system", "policy_adviser"];

const S = {
  runs: [], topo: null, status: { mode: "replay" }, sides: [], merged: [], pre: [], cursor: 0,
  playing: false, timer: null, selected: null, filter: {}, open: new Set(["agent:*"]), follow: false, followTimer: null,
};

/* ---------------------------------------------------------------- helpers */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const chip = (txt, cls = "", title = "") => `<span class="chip ${cls}" ${title ? `title="${esc(title)}"` : ""}>${esc(txt)}</span>`;
const recChips = (ids) => (ids || []).map((i) => (/^GAP-/.test(i) ? chip(i, "gap") : chip(i, "rec"))).join("");
const fmtT = (t) => "T+" + (Number.isInteger(t) ? t : (Math.round(t * 10) / 10));
const arr = (x) => (Array.isArray(x) ? x : x == null ? [] : [x]);
const last = (a) => (a.length ? a[a.length - 1] : undefined);
const sideName = (s) => (s.run.meta.rules === true ? "Rules on" : s.run.meta.rules === false ? "Rules off" : "Run");

async function jget(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(url + " " + r.status);
  return r.json();
}
function toast(msg) {
  const t = $("toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast.h); toast.h = setTimeout(() => (t.hidden = true), 4500);
}

/* ---------------------------------------------------------------- load */
async function init() {
  try {
    const [runs, topo, status] = await Promise.all([jget("/api/runs"), jget("/api/topology"), jget("/api/status")]);
    S.runs = runs.runs; S.topo = topo; S.status = status;
    fillPickers(runs.default);
  } catch (e) {
    $("main").innerHTML = `<div class="panel"><div class="empty">Could not reach the dashboard server: ${esc(e.message)}</div></div>`;
    return;
  }
  bind();
  const q = new URLSearchParams(location.search);       // ?run=NAME&compare=NAME&at=N|end  (deep links)
  if (q.get("run") && S.runs.some((r) => r.name === q.get("run"))) $("pickA").value = q.get("run");
  if (q.get("compare") && S.runs.some((r) => r.name === q.get("compare"))) $("pickB").value = q.get("compare");
  updatePairBtn();
  const a = $("pickA").value;
  if (a) {
    await loadSides(a, $("pickB").value);
    if (q.get("at")) setCursor(q.get("at") === "end" ? S.merged.length : +q.get("at") || 0);
  }
  if (!a) $("main").innerHTML = `<div class="panel"><div class="empty">No run files found. Put *.jsonl files in runs/ or start with --run FILE.</div></div>`;
}

function runLabel(r) {
  const bits = [r.name];
  if (r.rules === true) bits.push("rules on"); else if (r.rules === false) bits.push("rules off");
  if (r.source === "sample") bits.push("sample");
  return bits.join(" - ");
}
function fillPickers(def) {
  const pa = $("pickA"), pb = $("pickB");
  const runsOnly = S.runs.filter((r) => r.source !== "sample");
  const ordered = [...runsOnly, ...S.runs.filter((r) => r.source === "sample")];
  pa.innerHTML = ordered.map((r) => `<option value="${esc(r.name)}">${esc(runLabel(r))}</option>`).join("");
  pb.innerHTML = `<option value="">(none)</option>` + ordered.map((r) => `<option value="${esc(r.name)}">${esc(runLabel(r))}</option>`).join("");
  const pick = def && S.runs.some((r) => r.name === def) ? def : (ordered[0] || {}).name;
  if (pick) pa.value = pick;
  updatePairBtn();
}
function updatePairBtn() {
  const r = S.runs.find((x) => x.name === $("pickA").value);
  const b = $("pairBtn");
  if (r && r.pair && $("pickB").value !== r.pair) {
    b.hidden = false; b.textContent = r.rules ? "Compare with rules off" : "Compare with rules on"; b.dataset.pair = r.pair;
  } else b.hidden = true;
}

async function loadSides(a, b) {
  stop();
  const names = [a, b].filter(Boolean);
  try {
    const runs = await Promise.all(names.map((n) => jget("/api/run?name=" + encodeURIComponent(n))));
    S.sides = runs.map((run, i) => ({ key: "AB"[i], run, name: names[i] }));
  } catch (e) { toast("Could not load the run: " + e.message); return; }
  buildMerged();
  S.cursor = Math.min(S.cursor, S.merged.length);
  S.selected = null;
  render();
}

function buildMerged() {
  const m = [];
  S.sides.forEach((s, si) => s.run.events.forEach((e) => m.push({ si, idx: e.idx, epoch: e.epoch })));
  m.sort((x, y) => x.epoch - y.epoch || x.si - y.si || x.idx - y.idx);
  S.merged = m;
  S.pre = [];
  const cur = S.sides.map(() => -1);
  S.pre.push(cur.slice());
  for (const e of m) { cur[e.si] = e.idx; S.pre.push(cur.slice()); }
  $("slider").max = m.length;
}

/* ---------------------------------------------------------------- derived state at the cursor */
function nowEpoch() {
  if (S.cursor > 0) return S.merged[S.cursor - 1].epoch;
  return Math.min(...S.sides.map((s) => s.run.meta.start_epoch));
}
function visFor(si) { return (S.pre[S.cursor] || [])[si] ?? -1; }

function autonomyAt(run, vis, now) {
  let snap = run.autonomy[0];
  for (const a of run.autonomy) if (a.idx <= vis) snap = a;
  let mode = snap.mode, note = snap.note;
  if (!snap.killed && snap.expires_epoch && now > snap.expires_epoch && mode !== "MANUAL") { mode = "MANUAL"; note = "grant expired"; }
  return { mode, killed: !!snap.killed, note };
}
function netAt(run, vis) {
  let n = run.net[0];
  for (const x of run.net) if (x.idx <= vis) n = x;
  return n;
}
function approvalState(a, vis, now) {
  const hist = a.history.filter((h) => h.idx <= vis);
  const lastH = last(hist);
  let status = lastH ? lastH.status : "requested";
  let derived = null;
  if (status === "requested" && a.expires_epoch && now > a.expires_epoch) { status = "expired"; derived = "Nobody decided in time. The request clock ran out."; }
  if (status === "approved" && a.token_expires_epoch && now > a.token_expires_epoch) { status = "expired"; derived = "Approved, but the approval token ran out before the playbook ran."; }
  return { status, hist, derived };
}

/* ---------------------------------------------------------------- render */
function render() {
  if (!S.sides.length) return;
  const scrolls = {};
  document.querySelectorAll("[data-scroll]").forEach((el) => (scrolls[el.dataset.scroll] = el.scrollTop));
  const now = nowEpoch();
  const cmp = S.sides.length > 1;
  const main = $("main");
  const old = document.getElementById("cmpbar");
  if (old) old.remove();
  main.className = cmp ? "cmp" : "";
  main.innerHTML = S.sides.map((s, si) => sideHtml(s, si, now, cmp)).join("");
  if (cmp) main.insertAdjacentHTML("beforebegin", compareBar(now));
  document.querySelectorAll("[data-scroll]").forEach((el) => { if (scrolls[el.dataset.scroll] != null) el.scrollTop = scrolls[el.dataset.scroll]; });
  wireSide();
  controlsUpdate(now);
}

function controlsUpdate(now) {
  $("slider").value = S.cursor;
  $("pos").textContent = `${S.cursor} / ${S.merged.length}`;
  $("bPlay").innerHTML = S.playing ? "&#10074;&#10074; Pause" : "&#9654; Play";
  const e = S.cursor > 0 ? S.merged[S.cursor - 1] : null;
  const s0 = S.sides[0];
  if (!e) { $("nowline").innerHTML = "Press Play or Step to replay this run. Nothing has happened yet."; return; }
  const ev = S.sides[e.si].run.events[e.idx];
  const t = (now - s0.run.meta.start_epoch) / 60;
  $("nowline").innerHTML = `<b>${fmtT(Math.round(t * 10) / 10)} min</b> &middot; ${esc(ev.actor)}: ${esc(ev.summary)}`;
}

function sideHtml(s, si, now, cmp) {
  const run = s.run, vis = visFor(si);
  const evs = run.events.filter((e) => e.idx <= vis);
  const au = autonomyAt(run, vis, now);
  const t = (now - run.meta.start_epoch) / 60;
  const m = run.meta;
  const rulesTag = m.rules === true ? `<span class="tag on">Rules on</span>` : m.rules === false ? `<span class="tag off">Rules off</span>` : "";
  const head = `<div class="side-head"><h2>${esc(m.title || (m.scenario ? "Scenario " + m.scenario : s.name))} ${rulesTag}</h2>
      ${chip(s.name, "")} ${m.llm ? chip("LLM: " + m.llm) : ""} ${m.source === "sample" ? chip("sample trace, not a model run", "bad") : ""}</div>`;
  const chain = run.chain.ok === true ? chip("Audit chain intact", "ok") : run.chain.ok === false ? chip(run.chain.note, "bad") : chip("No hash chain", "");
  const modeCls = au.killed ? "KILLED" : au.mode;
  const killTxt = au.killed ? "Kill switch is ENGAGED" : "Kill switch is not engaged";
  const strip = `<div class="strip">
      <div class="kv">Clock<b>${fmtT(Math.round(Math.max(0, t) * 10) / 10)} min</b></div>
      <div class="kv">Events shown<b>${evs.length} of ${run.events.length}</b></div>
      <div class="kv">Autonomy mode<span class="mode ${esc(modeCls)}" title="${esc(au.note)}">${au.killed ? "MANUAL (kill switch)" : esc(au.mode)}</span></div>
      <div class="kv">Kill switch
        <span><button class="btn danger small" data-kill="${au.killed ? "release" : "engage"}" title="Replay: shows state only. Live mode: calls the commander kill switch.">${au.killed ? "Release" : "Kill switch"}</button>
        <span class="kill-state ${au.killed ? "on" : ""}">${killTxt}${S.status.mode === "replay" ? " (replay, state only)" : ""}</span></span></div>
      <div class="kv">Integrity<span>${chain}</span></div>
      ${run.stats.bad_lines ? `<div class="kv">Skipped lines<b>${run.stats.bad_lines}</b></div>` : ""}
    </div>`;
  const panels = [
    panelMap(run, vis), panelApprovals(run, vis, now, si), panelVerdicts(run, vis, si), panelGaps(run, vis, si),
    panelTimeline(run, vis, now, si), panelAgents(run, vis, si), panelMessages(run, vis, si), panelLog(run, evs, si),
  ];
  return `<section class="side" data-side="${si}">${head}${strip}<div class="grid">${panels.join("")}</div></section>`;
}

/* ---- compare */
function stats(run, vis, now) {
  const vs = run.verdicts.filter((v) => v.first_idx <= vis);
  const ap = run.approvals.filter((a) => a.requested_idx <= vis).map((a) => approvalState(a, vis, now).status);
  const cnt = (s) => ap.filter((x) => x === s).length;
  const msgs = run.messages.filter((m) => m.idx <= vis);
  return {
    "Verdicts from the rule engine": vs.length,
    "Conflicts caught": vs.filter((v) => v.verdict === "CONFLICT").length,
    "Gaps surfaced": run.gaps.filter((g) => g.first_idx <= vis).length,
    "Playbooks executed": cnt("executed"),
    "Plans refused or expired": cnt("refused") + cnt("expired") + cnt("rolled_back"),
    "Plans rejected by the commander": cnt("rejected"),
    "Messages sent": msgs.filter((m) => !m.rejected).length,
    "Messages refused": msgs.filter((m) => m.rejected).length,
    "Sites healed": Object.values(netAt(run, vis).sites).filter((x) => x.state === "healed").length,
    "Sites still down": Object.values(netAt(run, vis).sites).filter((x) => x.state === "down" || x.state === "attack").length,
  };
}
function compareBar(now) {
  const [a, b] = S.sides;
  const sa = stats(a.run, visFor(0), now), sb = stats(b.run, visFor(1), now);
  const rows = Object.keys(sa).map((k) => `<tr><td>${esc(k)}</td><td>${sa[k]}</td><td>${sb[k]}</td><td>${sa[k] !== sb[k] ? '<span class="diff">differs</span>' : ""}</td></tr>`).join("");
  return `<div class="cmpbar" id="cmpbar"><h2>Side by side at this moment</h2>
    <table><thead><tr><th>Measure</th><th>${esc(sideName(a))} (${esc(a.name)})</th><th>${esc(sideName(b))} (${esc(b.name)})</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

/* ---- network map */
function panelMap(run, vis) {
  const net = netAt(run, vis), T = S.topo;
  const W = 760, H = 400;
  const sx = (i) => 70 + i * 124, sy = 320, gy = 120;
  const gx = { "GW-IN-1": 150, "GW-IN-2": 400, "GW-XX": 650 };
  const ids = Object.keys(T.sites);
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Network map of six Chennai sites, two Indian gateways and one forbidden foreign gateway. Satellite links are emulated.">`;
  const col = (st) => STATE[st] || STATE.normal;
  // management network
  const mc = col(net.mgmt.state);
  svg += `<rect x="250" y="12" width="260" height="38" rx="8" fill="${mc[0]}" stroke="${mc[1]}" stroke-width="2"/>
    <text x="380" y="28" text-anchor="middle" font-size="12" font-weight="700">SAT-MGMT (operator management)</text>
    <text x="380" y="43" text-anchor="middle" font-size="11" fill="#444">${esc(mc[2])}</text>`;
  [["GW-IN-1", 150], ["GW-IN-2", 400]].forEach(([g, x]) => { svg += `<line x1="${x}" y1="${gy - 22}" x2="${g === "GW-IN-1" ? 300 : 380}" y2="50" stroke="#b8c2cf" stroke-dasharray="3 3"/>`; });
  // links
  ids.forEach((id, i) => {
    const st = net.sites[id], x1 = sx(i), y1 = sy - 26;
    ["A", "B"].forEach((p) => {
      const [kind, gw] = T.sites[id].paths[p];
      const active = st.path === p;
      const x2 = gx[gw], y2 = gy + 22;
      const sat = kind === "satellite";
      const w = active ? (kind === "fibre" ? 4 : 3) : 1.2;
      const colr = active ? (st.state === "healed" ? "#1b8a4a" : st.state === "down" || st.state === "attack" ? "#8e0000" : "#4a5a6e") : "#aab4c2";
      svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${colr}" stroke-width="${w}" ${sat ? 'stroke-dasharray="2 5" stroke-linecap="round"' : active ? "" : 'stroke-dasharray="7 4"'} opacity="${active ? 1 : 0.7}"/>`;
      if (sat && active) { const lx = x1 + (x2 - x1) * 0.3, ly = y1 + (y2 - y1) * 0.3; svg += `<text x="${lx}" y="${ly}" font-size="9" text-anchor="middle" fill="#33414f" stroke="#fff" stroke-width="3" paint-order="stroke">sat (emulated)</text>`; }
    });
  });
  // gateways
  Object.keys(T.gateways).forEach((g) => {
    const info = T.gateways[g], st = net.gateways[g] || { state: "normal" }, c = col(info.allowed ? st.state : "normal");
    const x = gx[g];
    svg += `<rect x="${x - 82}" y="${gy - 22}" width="164" height="44" rx="8" fill="${info.allowed ? c[0] : "#f1f1f1"}" stroke="${info.allowed ? c[1] : "#b00020"}" stroke-width="2" ${info.allowed ? "" : 'stroke-dasharray="5 4"'}/>
      <text x="${x}" y="${gy - 4}" text-anchor="middle" font-size="12" font-weight="700">${g}</text>
      <text x="${x}" y="${gy + 11}" text-anchor="middle" font-size="10" fill="#444">${info.allowed ? esc(info.role + ", India" + (st.state !== "normal" ? ", " + c[2] : "")) : "outside India: never allowed"}</text>`;
  });
  // sites
  ids.forEach((id, i) => {
    const st = net.sites[id], c = col(st.state), x = sx(i);
    svg += `<g><title>${esc(id + " " + T.sites[id].area + ": " + c[2] + (st.note ? ". " + st.note : ""))}</title>
      <rect x="${x - 54}" y="${sy - 26}" width="108" height="64" rx="8" fill="${c[0]}" stroke="${c[1]}" stroke-width="2.5"/>
      <text x="${x}" y="${sy - 8}" text-anchor="middle" font-size="12" font-weight="700">${id}</text>
      <text x="${x}" y="${sy + 5}" text-anchor="middle" font-size="10">${esc(T.sites[id].area)}</text>
      <text x="${x}" y="${sy + 19}" text-anchor="middle" font-size="10" font-weight="700" fill="#333">${esc(c[2])}</text>
      <text x="${x}" y="${sy + 32}" text-anchor="middle" font-size="9" fill="#555">path ${st.path} via ${esc(st.gateway)}</text></g>`;
  });
  svg += `<text x="10" y="${H - 8}" font-size="10" fill="#6b4e00">Emulated network. Dotted lines are emulated satellite links. Solid thick line = active path. Thin dashed = backup.</text></svg>`;
  const rows = ids.map((id) => {
    const st = net.sites[id], c = col(st.state);
    return `<tr><td><span class="sdot" style="background:${c[0]};border-color:${c[1]}"></span><b>${id}</b> ${esc(T.sites[id].area)}</td><td>${esc(c[2])}</td><td>path ${esc(st.path)} via ${esc(st.gateway)}</td><td>${esc(st.note || "")}</td></tr>`;
  }).join("");
  return `<div class="panel map span2"><h2>Network map (Chennai, emulated)</h2>${svg}
    <table class="maptable"><tbody>${rows}</tbody></table></div>`;
}

/* ---- approvals */
function approvalsHtml(run, vis, now) {
  const list = run.approvals.filter((a) => a.requested_idx <= vis);
  if (!list.length) return `<div class="empty">No approval requests yet.</div>`;
  const label = { requested: "Waiting for the commander", approved: "Approved", rejected: "Rejected", executed: "Executed",
    rolled_back: "Rolled back", refused: "Refused", expired: "Expired" };
  return list.slice().reverse().map((a) => {
    const { status, hist, derived } = approvalState(a, vis, now);
    const ap = hist.find((h) => h.status === "approved"), rj = hist.find((h) => h.status === "rejected");
    const ex = hist.find((h) => h.status === "executed" || h.status === "rolled_back");
    const rf = hist.filter((h) => h.status === "refused");
    let clock = "";
    if (status === "requested" && a.expires_epoch) {
      const win = Math.max(1, a.expires_epoch - a.requested_epoch), left = a.expires_epoch - now;
      clock = clockHtml("Request clock", left, win);
    } else if (status === "approved" && a.token_expires_epoch && ap) {
      const win = Math.max(1, a.token_expires_epoch - ap.epoch);
      clock = clockHtml("Approval token", a.token_expires_epoch - now, win);
    } else if (status === "expired" && derived) clock = `<div class="clock">${esc(derived)}</div>`;
    const decision = [];
    if (ap) decision.push(ap.auto ? `Auto-approved under an autonomy grant at ${fmtT(ap.t)}` : `Commander approved at ${fmtT(ap.t)}`);
    if (rj) decision.push(`Commander rejected at ${fmtT(rj.t)}: ${esc(rj.detail)}`);
    if (!ap && !rj && status === "requested") decision.push("No decision yet");
    const stages = ex && arr(ex.stages).length ? `<div class="stages">${arr(ex.stages).map((s) => `<span class="${s.healthy ? "" : "fail"}">${esc(s.pct)}%${s.healthy ? "" : " failed"}</span>`).join("")}</div>` : "";
    const ct = a.clone_test && a.clone_test.passed != null ? chip(a.clone_test.passed ? "clone test passed" : "clone test failed", a.clone_test.passed ? "ok" : "bad", a.clone_test.detail) : "";
    return `<div class="acard st-${esc(status)}"><div><span class="st">${esc(label[status] || status)}</span>
        ${chip(a.playbook, "rec")} <b>${esc(a.title || "")}</b></div>
      <div class="who">Owner ${esc(a.owner)} &middot; targets ${esc(arr(a.targets).join(", ") || "none")} &middot; asked at ${fmtT(a.requested_t)} ${ct}</div>
      ${a.reason ? `<div>${esc(a.reason)}</div>` : ""}
      ${clock}
      <div class="who">${decision.join(". ")}${ex ? `. ${ex.status === "executed" ? "Executed" : "Rolled back"} at ${fmtT(ex.t)}${ex.detail ? " (" + esc(ex.detail) + ")" : ""}` : ""}</div>
      ${rf.map((r) => `<div class="who" style="color:var(--bad)">Refused at ${fmtT(r.t)}: ${esc(r.detail)}</div>`).join("")}
      ${stages}</div>`;
  }).join("");
}
function clockHtml(name, leftSec, winSec) {
  const left = Math.max(0, leftSec), pct = Math.max(0, Math.min(100, (left / winSec) * 100));
  const cls = pct < 20 ? "low" : pct < 50 ? "mid" : "";
  return `<div class="clock">${esc(name)}: <b>${Math.round(left / 60)} min left</b> of ${Math.round(winSec / 60)}<div class="bar ${cls}"><i style="width:${pct}%"></i></div></div>`;
}
function panelApprovals(run, vis, now, si) {
  return `<div class="panel"><h2>Approvals <span class="count">${run.approvals.filter((a) => a.requested_idx <= vis).length}</span></h2>
    <div class="hint">A human approves every executable plan. Each request and each approval has a clock.</div>
    <div class="scroll" data-scroll="ap${si}">${approvalsHtml(run, vis, now)}</div></div>`;
}

/* ---- verdicts */
function panelVerdicts(run, vis, si) {
  const vs = run.verdicts.filter((v) => v.first_idx <= vis);
  let body;
  if (!run.meta.has_rule_engine) body = `<div class="empty">No rule engine in this run. Agents had no verdicts and cited no rule ids.</div>`;
  else if (!vs.length) body = `<div class="empty">No verdicts yet.</div>`;
  else body = vs.slice().reverse().map((v) => {
    const cls = VERDICTS.includes(v.verdict) ? v.verdict : "UNKNOWN";
    return `<div class="vcard ${cls}"><span class="v ${cls}">${esc(v.verdict || "UNKNOWN")}</span>
      <b>${esc(v.topic || v.rule_id || "")}</b> ${v.rule_id ? chip(v.rule_id, "rec") : ""}
      <div class="why">${esc(v.explanation)}</div>
      <div>Cites: ${recChips(v.record_ids) || '<span class="empty">no record</span>'} ${v.gap_id ? "Gap: " + chip(v.gap_id, "gap") : ""}</div>
      <div class="meta">${v.time_left ? esc(v.time_left) + ". " : ""}${arr(v.notes).map(esc).join(" ")} First at ${fmtT(v.first_t)}, seen by ${esc(v.seen_by.join(", "))}${v.repeats > 1 ? ", repeated " + v.repeats + " times" : ""}${v.kb_as_of ? ". KB as of " + esc(v.kb_as_of) : ""}</div></div>`;
  }).join("");
  const counts = Object.fromEntries(VERDICTS.map((x) => [x, vs.filter((v) => v.verdict === x).length]));
  const sum = VERDICTS.map((x) => `<span class="v ${x} ${counts[x] ? "" : "zero"}">${x.replace("_", " ")} ${counts[x]}</span>`).join("");
  const other = vs.filter((v) => !VERDICTS.includes(v.verdict)).length;
  return `<div class="panel span2"><h2>Rule-engine verdicts <span class="count">${vs.length}</span></h2>
    <div class="hint">Only the rule engine gives verdicts. Each one cites knowledge-base record ids.</div>
    <div class="vsum">${sum}${other ? `<span class="v UNKNOWN">OTHER ${other}</span>` : ""}</div>
    <div class="scroll tall" data-scroll="v${si}">${body}</div></div>`;
}

/* ---- timeline */
function lanesFor(run) {
  const seen = [];
  run.events.forEach((e) => { if (!seen.includes(e.actor)) seen.push(e.actor); });
  const rank = (a) => { const i = LANE_FIRST.indexOf(a); if (i >= 0) return i; const j = LANE_LAST.indexOf(a); return j >= 0 ? 1000 + j : 100 + seen.indexOf(a); };
  return seen.sort((a, b) => rank(a) - rank(b));
}
function panelTimeline(run, vis, now, si) {
  const lanes = lanesFor(run), LH = 24, L = 118, W = 860, R = 14, top = 6;
  const dur = Math.max(10, Math.ceil(run.stats.duration_min / 10) * 10);
  const H = top + lanes.length * LH + 26;
  const x = (t) => L + (Math.max(0, t) / dur) * (W - L - R);
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Timeline of events by minute and actor">`;
  lanes.forEach((a, i) => {
    const y = top + i * LH;
    svg += `<rect x="0" y="${y}" width="${W}" height="${LH}" fill="${i % 2 ? "#fff" : "#f7f9fb"}"/><text x="${L - 8}" y="${y + 16}" text-anchor="end" font-size="11">${esc(a)}</text>`;
  });
  for (let t = 0; t <= dur; t += dur > 60 ? 20 : 10) {
    svg += `<line x1="${x(t)}" y1="${top}" x2="${x(t)}" y2="${H - 22}" stroke="#e1e6ec"/><text x="${x(t)}" y="${H - 8}" text-anchor="middle" font-size="10" fill="#5b6776">T+${t}</text>`;
  }
  const slot = {};
  run.events.filter((e) => e.idx <= vis).forEach((e) => {
    const li = lanes.indexOf(e.actor), key = li + ":" + Math.round(e.t);
    const n = (slot[key] = (slot[key] || 0) + 1) - 1;
    const cx = x(e.t) + Math.min(n, 12) * 3.2, cy = top + li * LH + LH / 2;
    const sel = S.selected && S.selected.si === si && S.selected.idx === e.idx;
    svg += `<circle class="dot" data-idx="${e.idx}" cx="${cx}" cy="${cy}" r="${sel ? 6 : 4}" fill="${TYPE_COLOR[e.type] || "#999"}" stroke="${sel ? "#000" : "#fff"}" stroke-width="1"><title>${esc(fmtT(e.t) + " " + e.actor + ": " + e.summary)}</title></circle>`;
  });
  const nt = (now - run.meta.start_epoch) / 60;
  svg += `<line x1="${x(nt)}" y1="${top}" x2="${x(nt)}" y2="${H - 22}" stroke="#c62828" stroke-width="1.5" stroke-dasharray="4 3"/></svg>`;
  const legend = Object.keys(TYPE_LABEL).filter((k) => !["meta", "other", "net"].includes(k)).map((k) => `<span><i style="background:${TYPE_COLOR[k]}"></i>${TYPE_LABEL[k]}</span>`).join("");
  return `<div class="panel span3 tl"><h2>Scenario timeline <span class="count">events by minute and actor. Click a dot for details.</span></h2>${svg}<div class="legend">${legend}</div></div>`;
}

/* ---- agents */
function panelAgents(run, vis, si) {
  const cards = run.agents.map((a) => {
    const steps = a.steps.filter((s) => s.idx <= vis);
    if (!steps.length) return "";
    const key = `agent:${si}:${a.name}`;
    const calls = steps.filter((s) => s.type === "tool_call"), refused = calls.filter((s) => s.refused).length;
    const body = steps.slice().reverse().map((s) => {
      if (s.type === "task") return `<div class="step"><span class="tt" style="background:${TYPE_COLOR.task}">task</span> ${fmtT(s.t)} ${esc(s.text.slice(0, 260))}</div>`;
      if (s.type === "final") return `<div class="step"><span class="tt" style="background:${TYPE_COLOR.final}">answer</span> ${fmtT(s.t)}<div class="fin">${esc(s.rationale)}</div>
          ${s.cited.length || s.cited_rejected.length ? `<div>Cited: ${recChips(s.cited)}${s.cited_rejected.map((c) => chip(c + " (rejected)", "bad")).join("")}</div>` : ""}
          ${arr(s.stray_verdicts).length ? chip("verdict words not from the engine: " + s.stray_verdicts.join(", "), "bad") : ""}</div>`;
      return `<div class="step" data-open-event="${s.idx}"><span class="tt" style="background:${TYPE_COLOR.tool_call}">${esc(s.tool)}</span> ${fmtT(s.t)}
          ${s.refused ? chip("refused", "bad") : ""} ${esc(s.brief)}
          ${s.rationale ? `<div class="rat">Why: ${esc(s.rationale)}</div>` : ""}
          ${s.cited.length || s.cited_rejected.length ? `<div>Cited: ${recChips(s.cited)}${s.cited_rejected.map((c) => chip(c + " (rejected)", "bad")).join("")}</div>` : ""}</div>`;
    }).join("");
    return `<details class="agent" data-key="${esc(key)}" ${S.open.has(key) ? "open" : ""}><summary>${esc(a.name)}
        <span class="count">${steps.filter((s) => s.type === "task").length} tasks, ${calls.length} tool calls${refused ? ", " + refused + " refused" : ""}</span></summary>
        <div class="body">${body}</div></details>`;
  }).join("");
  return `<div class="panel span2"><h2>Agents <span class="count">${run.agents.length}</span></h2>
    <div class="hint">What each agent did, why, and which records it cited. Each agent sees different information.</div>
    <div class="scroll tall" data-scroll="ag${si}">${cards || '<div class="empty">No agent has acted yet.</div>'}</div></div>`;
}

/* ---- messages */
function panelMessages(run, vis, si) {
  const ms = run.messages.filter((m) => m.idx <= vis);
  const body = ms.length ? ms.slice().reverse().map((m) => `<div class="msg ${m.rejected ? "rej" : ""}" data-open-event="${m.idx}">
      <b>${esc(m.sender)}</b> <span class="arrow">to</span> <b>${esc(m.recipients.join(", "))}</b>
      ${chip(m.type || "message")} ${chip(m.data_class, "dc-" + m.data_class, "data class")} ${m.playbook ? chip(m.playbook, "rec") : ""}
      ${m.rejected ? chip("refused: " + (m.reason || ""), "bad") : ""} <span class="who">${fmtT(m.t)}</span>
      <div>${esc(m.text)}</div>${m.refs.length ? `<div>${recChips(m.refs.map((r) => (r.length > 40 ? r.slice(0, 12) + "..." : r)))}</div>` : ""}</div>`).join("")
    : `<div class="empty">No messages between agents yet.</div>`;
  return `<div class="panel"><h2>Messages <span class="count">${ms.length}</span></h2>
    <div class="hint">Who said what to whom, with the data class of each message.</div><div class="scroll tall" data-scroll="m${si}">${body}</div></div>`;
}

/* ---- gaps */
function panelGaps(run, vis, si) {
  const gs = run.gaps.filter((g) => g.first_idx <= vis);
  const ds = run.gap_drafts.filter((d) => d.idx <= vis);
  const regLabel = { confirmed: "human confirmed", rejected: "human rejected", candidate: "candidate" };
  const body = gs.length ? gs.map((g) => `<div class="msg">${chip(g.id, "gap")} ${g.register_status ? chip(regLabel[g.register_status] || g.register_status, g.register_status === "confirmed" ? "ok" : g.register_status === "rejected" ? "bad" : "") : ""}
      <b>${esc(g.title || "")}</b><div class="who">First at ${fmtT(g.first_t)} via ${esc(g.via.slice(0, 3).join("; "))}</div></div>`).join("")
    : `<div class="empty">No gap surfaced yet.</div>`;
  const dBody = ds.length ? `<h2 style="margin-top:10px">Gap drafts by agents <span class="count">${ds.length}</span></h2>` + ds.map((d) => {
    const hist = d.history.filter((h) => h.idx <= vis), st = last(hist) ? last(hist).status : d.status;
    return `<div class="msg"><b>${esc(d.id)}</b> ${chip(st, st === "confirmed" ? "ok" : st === "rejected" ? "bad" : "")} ${chip(d.topic)} <span class="who">by ${esc(d.by)}</span>
      <div>${esc(d.finding)}</div><div>Evidence: ${recChips(d.evidence)}</div></div>`;
  }).join("") : "";
  return `<div class="panel"><h2>Gaps surfaced <span class="count">${gs.length}</span></h2>
    <div class="hint">Places where the sources we checked say nothing or disagree. An agent pre-confirms a draft. Only a person confirms or rejects it.</div>
    <div class="scroll" data-scroll="g${si}">${body}${dBody}</div></div>`;
}

/* ---- event log */
function panelLog(run, evs, si) {
  const f = S.filter[si] || "all";
  const types = ["all", ...Object.keys(TYPE_LABEL)];
  const show = evs.filter((e) => f === "all" || e.type === f);
  const rows = show.slice(-250).reverse().map((e, i) => `<div class="row ${e.idx === evs[evs.length - 1].idx ? "new" : ""}" data-open-event="${e.idx}">
      <span class="t">${fmtT(e.t)}</span><span class="a">${esc(e.actor)}</span>
      <span class="k"><span class="tt" style="background:${TYPE_COLOR[e.type] || "#999"}">${esc(TYPE_LABEL[e.type] || e.type)}</span></span>
      <span class="s">${esc(e.summary)}</span></div>`).join("");
  return `<div class="panel span3"><h2>Event log <span class="count">${show.length} shown. Click a row for the raw entry.</span></h2>
    <div class="filter">Show <select data-filter="${si}">${types.map((t) => `<option value="${t}" ${t === f ? "selected" : ""}>${t === "all" ? "all events" : esc(TYPE_LABEL[t])}</option>`).join("")}</select></div>
    <div class="scroll tall" data-scroll="l${si}">${rows || '<div class="empty">Nothing yet.</div>'}</div></div>`;
}

/* ---------------------------------------------------------------- wiring */
function wireSide() {
  document.querySelectorAll("[data-open-event]").forEach((el) => el.addEventListener("click", () => {
    const si = +el.closest(".side").dataset.side;
    select(si, +el.dataset.openEvent);
  }));
  document.querySelectorAll(".dot").forEach((el) => el.addEventListener("click", () => select(+el.closest(".side").dataset.side, +el.dataset.idx)));
  document.querySelectorAll("details.agent").forEach((d) => d.addEventListener("toggle", () => { d.open ? S.open.add(d.dataset.key) : S.open.delete(d.dataset.key); }));
  document.querySelectorAll("[data-filter]").forEach((sel) => sel.addEventListener("change", () => { S.filter[sel.dataset.filter] = sel.value; render(); }));
  document.querySelectorAll("[data-kill]").forEach((b) => b.addEventListener("click", () => killClick(b.dataset.kill)));
}
function select(si, idx) {
  const ev = S.sides[si].run.events[idx];
  if (!ev) return;
  S.selected = { si, idx };
  $("detailTitle").textContent = `${S.sides[si].name} entry ${ev.seq}: ${ev.kind} by ${ev.actor} at ${fmtT(ev.t)}`;
  $("detailBody").textContent = JSON.stringify({ ts: ev.ts, kind: ev.kind, actor: ev.actor, payload: ev.payload }, null, 2);
  $("detail").hidden = false;
  render();
}

/* Kill switch hook. Replay: the server answers 409 and nothing changes. Live mode: the server calls the commander kill switch. */
async function killClick(action) {
  try {
    const r = await fetch(action === "release" ? "/api/kill/release" : "/api/kill", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason: "dashboard button" }) });
    const j = await r.json();
    toast(j.message || (j.ok ? "Done." : "Not done."));
  } catch (e) { toast("Could not reach the server."); }
}

/* ---------------------------------------------------------------- replay controls */
function setCursor(c) { S.cursor = Math.max(0, Math.min(S.merged.length, c)); render(); }
function stop() { S.playing = false; clearTimeout(S.timer); }
function tick() {
  if (!S.playing) return;
  if (S.cursor >= S.merged.length) { stop(); render(); return; }
  setCursor(S.cursor + 1);
  S.timer = setTimeout(tick, +$("speed").value);
}
function play() {
  if (S.playing) { stop(); render(); return; }
  if (S.cursor >= S.merged.length) S.cursor = 0;
  S.playing = true; render(); S.timer = setTimeout(tick, +$("speed").value);
}
function nextMilestone() {
  for (let c = S.cursor + 1; c <= S.merged.length; c++) {
    const e = S.merged[c - 1], ev = S.sides[e.si].run.events[e.idx];
    if (MILESTONE.has(ev.type)) return setCursor(c);
  }
  setCursor(S.merged.length);
}

function bind() {
  $("bPlay").onclick = play;
  $("bStep").onclick = () => { stop(); setCursor(S.cursor + 1); };
  $("bBack").onclick = () => { stop(); setCursor(S.cursor - 1); };
  $("bReset").onclick = () => { stop(); setCursor(0); };
  $("bEnd").onclick = () => { stop(); setCursor(S.merged.length); };
  $("bMile").onclick = () => { stop(); nextMilestone(); };
  $("slider").oninput = (e) => { stop(); setCursor(+e.target.value); };
  $("detailClose").onclick = () => { $("detail").hidden = true; S.selected = null; render(); };
  $("pickA").onchange = () => { S.cursor = 0; updatePairBtn(); loadSides($("pickA").value, $("pickB").value); };
  $("pickB").onchange = () => { S.cursor = 0; updatePairBtn(); loadSides($("pickA").value, $("pickB").value); };
  $("pairBtn").onclick = () => { $("pickB").value = $("pairBtn").dataset.pair; S.cursor = 0; updatePairBtn(); loadSides($("pickA").value, $("pickB").value); };
  $("follow").onchange = (e) => { S.follow = e.target.checked; clearInterval(S.followTimer); if (S.follow) S.followTimer = setInterval(followTick, 2000); };
  document.addEventListener("keydown", (e) => {
    if (/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName) && e.key !== " ") return;
    if (e.target.tagName === "BUTTON" && e.key === " ") return;
    if (e.key === " ") { e.preventDefault(); play(); }
    else if (e.key === "ArrowRight") { stop(); setCursor(S.cursor + 1); }
    else if (e.key === "ArrowLeft") { stop(); setCursor(S.cursor - 1); }
    else if (e.key === "Home") { stop(); setCursor(0); }
    else if (e.key === "End") { stop(); setCursor(S.merged.length); }
  });
}

/* Follow mode: re-read the run files every 2 s (a runner may still be writing). Stays at the end if you were at the end. */
async function followTick() {
  if (!S.sides.length) return;
  const atEnd = S.cursor >= S.merged.length;
  try {
    S.runs = (await jget("/api/runs")).runs;
    const names = S.sides.map((s) => s.name);
    const runs = await Promise.all(names.map((n) => jget("/api/run?name=" + encodeURIComponent(n))));
    if (runs.every((r, i) => r.stats.entries === S.sides[i].run.stats.entries)) return;
    S.sides = runs.map((run, i) => ({ key: "AB"[i], run, name: names[i] }));
    buildMerged();
    S.cursor = atEnd ? S.merged.length : Math.min(S.cursor, S.merged.length);
    render();
  } catch (e) { /* server busy or file mid-write: try again next tick */ }
}

init();
