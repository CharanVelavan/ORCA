"""Apply the approved dashboard and dimension update to an existing v7 report.

Usage: python submission/update_v7.py /path/to/ORCA-NTN-report-v7.docx
Preserves the existing document template, figures, tables and paragraph properties.
Export and visually verify the PDF separately; the submission limit is five pages.
"""
from copy import deepcopy
from pathlib import Path
import sys
from zipfile import ZipFile
import xml.etree.ElementTree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
N = {'w': W}
Q = lambda tag: f'{{{W}}}{tag}'
MAPPING = ('Nine selected Readiness 2.0 dimensions [5] map to implemented capabilities: '
           'cross-domain evidence (D3), context (D4), human interface (D6), role objectives (D7), '
           'AI collaboration (D8), human decisions (D9), policy checks (D10), emergency-service '
           'protection (D11) and digital infrastructure (D13). These are capability mappings, '
           'not official readiness scores; each recorded run needs its own evidence.')

def text(element):
    return ''.join(t.text or '' for t in element.findall('.//w:t', N))

def set_text(paragraph, value):
    runs = paragraph.findall('w:r', N)
    regular = next((r for r in runs if r.find('w:rPr/w:b', N) is None), runs[0] if runs else None)
    props = regular.find('w:rPr', N) if regular is not None else None
    for child in list(paragraph):
        if child.tag != Q('pPr'):
            paragraph.remove(child)
    run = ET.SubElement(paragraph, Q('r'))
    if props is not None:
        run.append(deepcopy(props))
    rp = run.find('w:rPr', N)
    if rp is None:
        rp = ET.SubElement(run, Q('rPr'))
    for tag in ('b', 'bCs'):
        item = rp.find('w:' + tag, N)
        if item is None:
            item = ET.SubElement(rp, Q(tag))
        item.set(Q('val'), '0')
    ET.SubElement(run, Q('t')).text = value

def update(path):
    with ZipFile(path) as source:
        parts = {item.filename: (item, source.read(item)) for item in source.infolist()}
    xml = parts['word/document.xml'][1]
    import re
    for prefix, uri in re.findall(r'xmlns:([\w]+)="([^"]+)"', xml.decode()):
        ET.register_namespace(prefix, uri)
    root = ET.fromstring(xml)
    body = root.find('w:body', N)
    paragraphs = body.findall('w:p', N)
    title = paragraphs[0]
    if 'forNTN' in text(title):
        # Repair this existing missing space without changing title formatting.
        for node in title.findall('.//w:t', N):
            if node.text and 'forNTN' in node.text:
                node.text = node.text.replace('forNTN', 'for NTN')
    changes = {
        ('Non-terrestrial networks (NTN) now carry', 'Non-terrestrial networks (NTN) carry'): ('Non-terrestrial networks (NTN) carry mobile, payment, '
            'hospital, utility and emergency traffic where fibre cannot reach. Terminals, direct-to-device links '
            'and integrated gateways are advancing. Cyber security lags: the cited 3GPP study leaves feeder-link '
            'and inter-satellite-link security unspecified [14], while India’s space cyber framework is advisory [16].'),
        ('A fault and an attack look alike', 'Faults and attacks can look alike'): ('Faults and attacks can look alike but trigger different duties. '
            'Fixed failover may select an attacker-controlled backup. Institutions see different evidence and '
            'reporting triggers. In KA-SAT (2022), attackers reached the operator’s ground management network '
            'through a misconfigured VPN and disabled tens of thousands of terminals [1].'),
        ('ORCA-NTN (Orchestrated Response',): ('ORCA-NTN (Orchestrated Response and Coordination Agents) '
            'provides cyber-aware coordination and secure self-healing for NTN. Models detect causes; institution '
            'agents retrieve and explain law; deterministic rules return cited verdicts. Humans approve fixes '
            'and policy recommendations. Recovery checks backup integrity; candidate gaps retain evidence. '
            'Ten recorded scenarios reached 40 expected verdicts without unapproved execution. All links are '
            'emulated. India supplies the rules and gap register; EU, US and UAE sources provide comparisons.'),
        ('This section explains ORCA-NTN in detail.', 'Figure 2 maps ORCA-NTN'): ('Figure 2 maps ORCA-NTN '
            'onto Y.3172 [2]. Detect (1–4): per-minute link, rain, battery, login, GNSS and packet-loss observations '
            'become 36 features, including a P.838 rain-fade residual [13]. M1–M4 assess them and route scoped '
            'alerts. Assess (5–7): institution agents retrieve evidence; YAML rules return six possible cited '
            'verdicts. Recover (8–11): owners propose 17 fixed playbooks. Human approval creates a one-use, '
            'exact-plan token, valid 15 minutes. Clone and clean-path tests precede 5/25/100% rollout, re-attack '
            'checks and automatic rollback on failure. Coordinate (12): agents draft notices and evidence; '
            'humans confirm gaps and sign recommendations. A hash-chained trail records actions.'),
        ('Output.', 'Dashboard.'): ('Dashboard. Scenario briefings lead into a shared exercise console: '
            'observed sites, model alerts, cited agent explanations, reporting clocks, recovery and audit. '
            'A director rail launches emulated conditions and stops future effects. A six-checkpoint judge '
            'walkthrough tracks evidence review; recording exports retain public facts and explicit integrity limits. '
            'Replay remains read-only.'),
        ('Tuned Qwen reached 40/40',): ('Planned dimension coverage is 5/9 for S0, 8/9 for N2 and N3, '
            'and 9/9 for the other seven scenarios. S0 excludes D6/D8/D9/D11; N2/N3 exclude D11. '
            'Names alone do not prove human impact or inclusion. Qwen reached 40/40 expected verdicts '
            'with rules versus 0/40 without; neither comparison arm executed a playbook. Approved recovery '
            'is demonstrated separately. Planned coverage is not an observed-run result.'),
        ('Hybrid ML and AI agents.',): ('Hybrid ML and AI agents. ML reads numerical telemetry each minute; '
            'LLM agents retrieve clauses, explain model reasons and draft notices. Deterministic rules evaluate '
            'policy. M1 learns normal behaviour without attack labels. M3 classifies causes, gives SHAP reasons '
            'and abstains when unsure. M2 forecasts with uncertainty; M4 optimises auditable priorities. '
            'M1–M3 train on emulator data and face harder held-out tests (Table 1); M2 also uses a daily '
            'tier trained on ITU sandbox Turkcell data [3].'),
        ('The agents.',): ('The agents. Each institution has its own view and powers (Table 2). Events wake '
            'agents to read alerts, retrieve evidence, evaluate rules and request owner-specific playbooks or '
            'notices. Code checks calls and citations. AI explains clauses, deadlines, model reasons and '
            'coverage limits. Humans interpret ambiguity, confirm gaps, judge proportionality and sign '
            'recommendations; agents cannot assume these powers.'),
        ('Knowledge base and RAG.',): ('Knowledge base and RAG. Three layers hold 369 official sources '
            'with authority, legal status and hash; verified quoted records and triggers for the rule engine; '
            'and a gap register. Country rules are separate YAML files. Retrieval spans 82,191 clause-level '
            'chunks using Qwen3-Embedding-8B vectors, keyword search and reranking. Each chunk retains law '
            'and clause path. Named-clause retrieval and abstention support traceability '
            '(recall@5 0.70; exact citations 5/5).'),
        ('Agents retrieve relevant clauses and explain coverage limits;',): ('Agents retrieve clauses and explain '
            'coverage limits; humans confirm gaps and sign recommendations. Candidate findings retain a search '
            'record, impact analysis, global comparison and interim action. Table 5 summarises seven confirmed '
            'findings within the Indian sources checked as of 7 Nov 2026; absence in that search is not proof '
            'that no rule exists.'),
        ('Standards gaps and global comparison.',): ('Standards gaps and global comparison. A standard '
            'machine-readable policy-rule format was not found in the sources checked; ORCA uses YAML. '
            'NIS2 provides 24-hour/72-hour reports [10]; UAE TDRA prioritises emergency calls at '
            'interconnection [12]. Nineteen EU, US, California, UAE and ITU examples support the seven '
            'confirmed gap records (kb/gaps/COVERAGE.md).'),
    }
    for prefixes, replacement in changes.items():
        matches = [p for p in paragraphs if text(p) == replacement or any(text(p).startswith(prefix) for prefix in prefixes)
                   or prefixes[0].startswith('Tuned Qwen') and text(p).startswith('Planned dimension coverage is')]
        if len(matches) != 1:
            raise ValueError(f'Expected one paragraph for {prefixes}, found {len(matches)}')
        set_text(matches[0], replacement)
    previous = next((p for p in paragraphs if text(p).startswith('Nine selected Readiness 2.0 dimensions')), None)
    if previous is not None:
        set_text(previous, MAPPING)
        paragraph = previous
    else:
        caption = next(p for p in paragraphs if text(p).startswith('Table 3.'))
        base = next(p for p in paragraphs if text(p).startswith('Dashboard.'))
        paragraph = deepcopy(base)
        set_text(paragraph, MAPPING)
        body.insert(list(body).index(caption), paragraph)
    pp = paragraph.find('w:pPr', N)
    if pp is None:
        pp = ET.SubElement(paragraph, Q('pPr'))
    if pp.find('w:keepLines', N) is None:
        ET.SubElement(pp, Q('keepLines'))
    for heading in paragraphs:
        if text(heading).startswith(('Mapping with ITU-T', 'Standards mapping e.g.')):
            hp = heading.find('w:pPr', N)
            if hp is None:
                hp = ET.SubElement(heading, Q('pPr'))
            if hp.find('w:keepNext', N) is None:
                ET.SubElement(hp, Q('keepNext'))
    # Keep the established 12-point body and one-inch margins. Remove repeated prose,
    # then reduce illustration space proportionally rather than shrinking body type.
    wp = {'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
          'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    for drawing, max_height in zip(root.findall('.//w:drawing', N), [2.15, 2.65]):
        extent = drawing.find('.//wp:extent', wp)
        if extent is not None:
            target_height = int(max_height * 914400)
            height = int(extent.attrib['cy'])
            if height > target_height:
                ratio = target_height / height
                extent.set('cx', str(round(int(extent.attrib['cx']) * ratio)))
                extent.set('cy', str(target_height))
                for size in drawing.findall('.//a:xfrm/a:ext', wp):
                    size.set('cx', extent.attrib['cx'])
                    size.set('cy', extent.attrib['cy'])
    # Keep the report's harder-test false-alarm figure aligned with the current
    # benchmark file after the validated M1 threshold update.
    for node in root.findall('.//w:t', N):
        if node.text and '2.3% false alarms' in node.text:
            node.text = node.text.replace('2.3% false alarms', '1.2% false alarms')
    output = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    temp = path.with_suffix('.updated.docx')
    with ZipFile(temp, 'w') as target:
        for name, (info, data) in parts.items():
            target.writestr(info, output if name == 'word/document.xml' else data)
    temp.replace(path)
    print(f'Updated {path.name}')

if __name__ == '__main__':
    update(Path(sys.argv[1]).resolve())
