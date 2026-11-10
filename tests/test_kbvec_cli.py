"""The documented evaluation flags reach the evaluator without requiring an index."""
import sys
from types import SimpleNamespace

import pytest

from orca.kbvec import __main__ as cli


@pytest.mark.parametrize('command', ['eval', 'evaluate'])
def test_v2_evaluation_flag_reaches_v2_runner(monkeypatch, capsys, command):
    calls = []
    fake = SimpleNamespace(run_v2=lambda **kw: calls.append(kw) or {'tested': True})
    monkeypatch.setitem(sys.modules, 'orca.kbvec.evaluate', fake)
    import orca.kbvec
    monkeypatch.setattr(orca.kbvec, 'evaluate', fake, raising=False)
    monkeypatch.setattr(sys, 'argv', ['orca.kbvec', command, '--v2', '--tier', 'corpus', '--no-rerank'])
    cli.main()
    assert calls == [{'rerank': False, 'tier': 'corpus'}]
    assert '"tested": true' in capsys.readouterr().out


def test_legacy_evaluation_does_not_require_v2_attribute(monkeypatch, capsys):
    calls = []
    fake = SimpleNamespace(run=lambda **kw: calls.append(kw) or [], table=lambda _: 'legacy evaluation')
    monkeypatch.setitem(sys.modules, 'orca.kbvec.evaluate', fake)
    import orca.kbvec
    monkeypatch.setattr(orca.kbvec, 'evaluate', fake, raising=False)
    monkeypatch.setattr(sys, 'argv', ['orca.kbvec', 'eval'])
    cli.main()
    assert calls == [{'rerank': True, 'tier': None, 'dedupe': True}]
    assert 'legacy evaluation' in capsys.readouterr().out
