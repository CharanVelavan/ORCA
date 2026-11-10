# Windows quick start

Run these commands in **PowerShell or Command Prompt** from the ORCA checkout. Use 64-bit Python 3.12. The launcher first tries `py -3.12`; it accepts `python` only when that command is Python 3.12. The [Python Windows guide](https://docs.python.org/3.12/using/windows.html) explains the installer and launcher. Python.org provides a [3.12.10 Windows installer](https://www.python.org/downloads/release/python-31210/); later 3.12 security releases may be source-only.

```powershell
.\quickstart.bat
```

The default starts the mock-agent dashboard at <http://127.0.0.1:8060/>. It does not require a model server or a model/index download. The first setup creates the isolated `.venv-judge` and installs the hash-checked `requirements-judge.lock` dependencies; allow network access and time for installation. If the network-model cache is missing, the first server start can also train the emulated network models and take several minutes. All network links are emulated.

To inspect the environment without installing or starting the dashboard, or to preview the planned actions, run either:

```powershell
.\quickstart.bat --check
.\quickstart.bat --dry-run
```

To use a running OpenAI-compatible model endpoint for the next exercise, supply **both** its base URL and the exact model ID exposed by that endpoint:

```powershell
.\quickstart.bat --mode live --endpoint http://127.0.0.1:8000/v1 --model-id "your-exact-served-model-id"
```

For a local model server, first install a compatible `llama-server.exe` yourself. The helper can then download the verified model, start that executable and stop it when the dashboard exits:

```powershell
.\quickstart.bat --download-model --serve-model --llama-server "C:\path with spaces\llama-server.exe"
```

This uses CPU by default. Add `--gpu-layers N` only with a compatible GPU build and driver; choose `N` for the available hardware. Port 8000 must be free. The helper uses the exact local model alias `orca-ntn-qwen-ft`. Installing the server binary is a separate step.

The model server is separate from the dashboard. The [llama.cpp server guide](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) documents its Windows executable and model-path syntax. A compatible CPU build can run without a GPU, but a model of this size needs substantial memory and CPU inference can be slow. GPU builds require a compatible device, driver and matching backend. Do not put API keys in command arguments; use the application’s Model connection or the environment variable documented by the helper.

With Python and a compatible `llama-server.exe` already installed, the complete optional local model
and RAG path is:

```powershell
.\quickstart.bat --download-model --serve-model --download-rag --prepare-rag --download-embedding --serve-embedding --llama-server "C:\path with spaces\llama-server.exe"
```

This also downloads the 4.68 GB Qwen3-Embedding-8B Q4 GGUF and serves it on port 1235 with the exact
ID `text-embedding-qwen3-embedding-8b`. It is a separate CPU service from chat. Allow roughly 35 GB
or more free disk space for all files, index and caches; 32 GB RAM can be tight and 48 GB is a more
comfortable planning allowance for both services and retrieval. These are estimates, not measured
Windows minimums. Quantized query embeddings can change retrieval rankings. To use an existing
embedding service instead, supply `--embedding-endpoint URL --embedding-model ID` and omit
`--serve-embedding`; use `ORCA_EMBED_KEY` privately for authentication if required.

Optional downloads are explicit:

```powershell
.\quickstart.bat --download-model --download-only
.\quickstart.bat --download-rag --prepare-rag --download-only
```

The model file is approximately 19.2 GB (17.9 GiB) before server memory overhead. The RAG snapshot is approximately 0.93 GB before cache and index overhead. Allow extra free disk space. The repository’s model is Apache 2.0; the RAG dataset contains mixed-source material, so review its source terms before reuse. Omit `--download-only` to start the dashboard after the requested downloads. The model is saved in `models/llm/qwen-ft`; downloading it does not start a model server. The RAG files are saved in `kb/vec_build`; `--prepare-rag` imports them into local Chroma and snapshots the index. Alternatively, after a download without `--prepare-rag`, create the local index with `.\.venv-judge\Scripts\python.exe -m orca.kbvec load-vectors` and then `.\.venv-judge\Scripts\python.exe -m orca.kbvec snapshot`. A separate compatible embedding endpoint is needed for live vector queries; mock mode does not need one. The [Hugging Face download guide](https://huggingface.co/docs/huggingface_hub/main/guides/download) describes its cache and `HF_HOME` setting.

If `py -3.12 --version` fails, install Python 3.12 with the launcher, open a new terminal, and try again. Use a normal per-user installation where possible; the launcher does not request administrator rights or install Python. If a native DLL fails to load, check the error and install the matching [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist/) only if your installed component requires it. OpenMP and GPU runtime requirements depend on the chosen native package or model-server build; follow that build’s official installation instructions instead of installing unrelated runtimes by default.

The Windows launcher has been statically checked, but has not yet been executed on Windows. A universal dependency lock and cross-platform resolver checks do not establish native execution. Report the exact failing command and non-secret error text if setup fails. See [RUN.md](RUN.md) for current evaluation commands, [JUDGE_REPRODUCIBILITY.md](JUDGE_REPRODUCIBILITY.md) for pinned artifacts and server setup, [JUDGE_VERIFICATION.md](JUDGE_VERIFICATION.md) for actual verification evidence, and [DEMO.md](DEMO.md) for the exercises.
