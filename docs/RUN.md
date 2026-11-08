# ORCA-NTN: Judge & Evaluator Run Guide

This guide provides step-by-step instructions to run and evaluate **ORCA-NTN** (Orchestrated Response and Coordination Agents for Non-Terrestrial Networks).

> [!IMPORTANT]
> **Emulation Notice:** Every satellite and non-terrestrial network (NTN) link in ORCA-NTN is strictly **emulated** within a software sandbox. No live orbital assets, commercial satellite constellations, or physical telecommunications infrastructure are accessed or controlled.

---

## 1. Quick Start via Docker Compose (Recommended)

Docker Compose provides a reproducible environment that runs the entire testbed on one machine, including the ORCA-NTN application and a persistent ChromaDB vector store.

### Prerequisites
- Docker Engine 24.0+ / Docker Desktop (verified with Docker version 29.5.3)
- Docker Compose v2.20+

### Step 1: Clone and Enter the Repository
```bash
git clone <repo-url>
cd orca-ntn
```

### Step 2: Configure Environment (Optional)
By default, ORCA-NTN runs in **offline mock mode** requiring no external API keys, internet connectivity, or credentials.

To set an optional Commander PIN hash or configure external endpoints, copy the template:
```bash
cp .env.example .env
```
*(Never bake secrets or tokens into images; Compose automatically pulls variables from `.env` without printing or storing plaintext PINs.)*

### Step 3: Run with Docker Compose
To build the image and run the default demo scenario (`S1`):
```bash
docker compose up --build
```
Or to run via an ephemeral one-off container:
```bash
docker compose run --rm orca
```

### Step 4: Run Any Specific Scenario in Docker
You can execute any of the 10 scenarios (`S0`–`S3`, `N1`–`N5`, `CAP`) directly:
```bash
# Run scenario S1 with deterministic rule engine
docker compose run --rm orca python run_demo.py --scenario s1

# Run scenario S1 without rules (baseline comparison)
docker compose run --rm orca python run_demo.py --scenario s1 --no-rules

# Run full capability scenario
docker compose run --rm orca python run_demo.py --scenario cap
```

### Step 5: Stop Services
```bash
docker compose down
```
ChromaDB state is persisted to the local `./chroma` directory across container restarts.

---

## 2. Quick Start via Local Python Environment

If you prefer running directly on your host machine using a Python virtual environment:

### Prerequisites
- Python 3.12 (Python 3.11+ supported for core rules/tests; 3.12 recommended for vector KB)
- Git

### Step 1: Set Up Virtual Environment
```bash
cd orca-ntn
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
*(On Debian/Ubuntu Linux systems, ensure `libgomp1` is installed: `sudo apt-get install -y libgomp1` for LightGBM OpenMP support).*

### Step 2: Run the Verification Suite
Run the test suite offline with mock LLM:
```bash
python -m pytest -q
```
*Expected result:* 227+ passed (offline deterministic test double, zero external network calls).

### Step 3: Validate the Knowledge Base
Ensure all regulatory records and citations meet strict schema criteria:
```bash
python tools/validate_kb.py
```
*Expected result:* `OK` (validates all jurisdiction records, gaps, and verified official quotes).

### Step 4: Verify Scenario Consistency
Replay all 10 scenario event streams and evaluate state consistency:
```bash
python scenarios/check_scen.py
```
*Expected result:* 0 problems across all scenarios (`CAP`, `N1`–`N5`, `S0`–`S3`).

---

## 3. Running Scenarios (S0–S3, N1–N5, CAP)

ORCA-NTN includes ten reproducible scenarios testing automated fault vs. attack classification, regulatory compliance, multi-agency coordination, and gap detection.

### Scenario Descriptions

| Scenario | Description | Key Focus |
|---|---|---|
| **S0** | Baseline Clean Run | Normal network conditions, zero false-alarm gap triggers |
| **S1** | Multi-Operator Cyber Incident | Space ground-segment attack, reporting clocks, cross-sector coordination |
| **S2** | Priority & Conflict Resolution | Competing emergency vs. critical-infrastructure traffic routing |
| **S3** | Regulatory Regime Swap | Comparative analysis across jurisdictions (e.g. India vs. Global/EU) |
| **N1** | Weather Fade vs. Jamming | Anomaly detection differentiating rain fade from uplink jamming |
| **N2** | Cascading Power Outage | Backhaul battery depletion and critical-load shedding |
| **N3** | Ground Segment Misconfiguration | VPN credential misuse and terminal unresponsiveness |
| **N4** | Coordinated Physical + Cyber Attack | Multi-site simultaneous failover and path validation |
| **N5** | Downstream Supply Chain Breach | Third-party maintenance vector and notification propagation |
| **CAP** | Full Capability Benchmark | End-to-end evaluation covering all 9 regulatory gap categories |

### Execution Commands

Run any scenario using `run_demo.py`:

```bash
# Core Scenarios
python run_demo.py --scenario s0
python run_demo.py --scenario s1
python run_demo.py --scenario s2
python run_demo.py --scenario s3

# Network & Threat Scenarios
python run_demo.py --scenario n1
python run_demo.py --scenario n2
python run_demo.py --scenario n3
python run_demo.py --scenario n4
python run_demo.py --scenario n5

# Full Capability Scenario
python run_demo.py --scenario cap
```

### With Rules vs. Without Rules Comparison
ORCA-NTN demonstrates the critical necessity of a deterministic policy engine over raw LLM reasoning:

1. **With Rules (Default):**
   ```bash
   python run_demo.py --scenario s1
   ```
   *Output:* Deterministic verdicts (`COMPLIANT`, `CONFLICT`, `AMBIGUITY`, `POTENTIAL_GAP`) verified against exact KB record citations (`GAP-IN-01`, `GAP-IN-02`, `GAP-IN-09`).

2. **Without Rules Baseline (`--no-rules`):**
   ```bash
   python run_demo.py --scenario s1 --no-rules
   ```
   *Output:* Rule engine bypassed; agent prompts execute without statutory constraints, revealing missed gap detections and ungrounded coordination decisions.

Every execution produces an immutable, SHA-256 chained audit trail stored in `runs/<SCENARIO>-<mode>.jsonl`.

---

## 4. LLM Configuration Modes

ORCA-NTN supports multiple execution backends depending on judge environment and hardware availability:

### Option 1: Deterministic Offline Mock (Default & Recommended for Judges)
- **Zero setup:** Default flag `--llm mock`.
- **Zero cost & network:** Operates completely offline with no API keys or local LLM servers.
- **Deterministic:** Provides identical, reproducible verdicts across any operating system.
```bash
python run_demo.py --scenario s1 --llm mock
```

### Option 2: Local LM Studio (Local Inference)
If evaluating with a local model on your laptop:
1. Launch **LM Studio** and start the local server on `http://localhost:1234/v1`.
2. Load `qwen2.5-14b-instruct` (or similar OpenAI-compatible model) and nomic embedding model.
3. Configure your environment:
   ```bash
   export LLM_BASE_URL="http://localhost:1234/v1"
   export LLM_MODEL="qwen2.5-14b"
   ```
4. Run:
   ```bash
   python run_demo.py --scenario s1 --llm local
   ```

### Option 3: Hosted Qwen Endpoint (Cloud / Atlas Tunnel)
For live high-capacity evaluations using the hosted Qwen model (e.g., Qwen3.6-35B-A3B on Google Cloud via IAP/SSH tunnel):
1. Establish the tunnel to the evaluation VM:
   ```bash
   # Tunnel exposes hosted endpoint on localhost:8000
   ```
2. Configure environment:
   ```bash
   export LLM_BASE_URL="http://localhost:8000/v1"
   export LLM_MODEL="Qwen/Qwen3.6-35B-A3B"
   ```
3. Run:
   ```bash
   python run_demo.py --scenario s1 --llm local
   ```

### Option 4: Exact Replay Mode (`LLM_MODE=replay`)
To inspect pre-recorded high-parameter live runs without active network calls:
```bash
export LLM_MODE=replay
python run_demo.py --scenario s1 --llm local
```
*Note:* Replay mode loads cryptographic matches from `data/llm_cache/`. If a new prompt is sent that has not been cached, it informs you to record it with `LLM_MODE=record`.

---

## 5. Vector Knowledge Base (ChromaDB)

The vector KB (`orca.kbvec`) stores clause embeddings for semantic search and gap discovery over official regulatory texts.

- **Persistent storage:** Located in `./chroma` (and mounted into `/app/chroma` in Docker).
- **Ingest:** Embeds official source documents and verified records.
- **Query:** Fast retrieval of relevant regulatory clauses and binding directions.

Example query using local virtualenv:
```bash
python -m orca.kbvec query "6 hour incident reporting window" --filter jurisdiction=IN
```

---

## 6. Security and Compliance Rules

- **PIN Security:** The incident commander PIN is never stored or logged in plain text. Only `ORCA_COMMANDER_PIN_SHA256` is ingested via environment or `.env`.
- **Read-Only Verification:** Hard-coded guardrails prevent modification of verified records in `kb/` during scenario execution.
- **Audit Verification:** All actions, verdicts, and tool invocations append to a hash-chained audit log verifiable via `orca.audit.AuditLog.verify()`.
