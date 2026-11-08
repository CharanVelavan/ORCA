# RAG v2 Colab GPU build

Run each cell in order on an A100 runtime. This embeds only the offline corpus; every NTN reference remains emulated.

```python
from google.colab import drive
drive.mount('/content/drive')
```

```bash
!git clone <YOUR-REPOSITORY-URL> /content/orca-ntn
%cd /content/orca-ntn
!pip -q install sentence-transformers transformers accelerate pymupdf beautifulsoup4 pyyaml numpy
```

```bash
# Upload this repository file into the Colab session, then copy it into the clone.
!cp /content/embed_corpus.py /content/orca-ntn/finetune/colab/embed_corpus.py
!test -f /content/drive/MyDrive/orca-ft/rag/orca-corpus.zip
!ORCA_REPO=/content/orca-ntn python finetune/colab/embed_corpus.py
```

```python
# Verify the portable payload before downloading MyDrive/orca-ft/rag/out/.
import json, numpy as np
out = '/content/drive/MyDrive/orca-ft/rag/out'
ids = json.load(open(out + '/ids.json'))
vectors = np.load(out + '/embeddings.f16.npy')
assert len(ids) == len(vectors) and np.isfinite(vectors).all()
assert np.allclose(np.linalg.norm(vectors.astype('float32'), axis=1), 1, atol=3e-3)
print(len(ids), vectors.shape, json.load(open(out + '/model.json')))
```

Download `chunks.jsonl`, `embeddings.f16.npy`, `ids.json`, `model.json`, `questions_v2.f16.npy`,
`questions_v2_ids.json`, and `reranker_4b_scores.json` to `kb/vec_build/` locally. Then run:

```bash
python -m orca.kbvec load-vectors
python -m orca.kbvec snapshot
python -m orca.kbvec eval --v2 --tier corpus
```

Record the corresponding v1 collection run separately; only make v2 default if the documented recall,
negative-accuracy, and p95 latency gates pass.
