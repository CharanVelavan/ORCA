# Judge release

`judge-v1.0.0` is the post-submission verification release. The approved submitted PDF is preserved
unchanged; the release adds tested fixes, frozen evaluation inputs and evidence. The originally
submitted implementation/showcase commits remain recorded separately in the manifest.

```sh
git clone -c core.autocrlf=false --branch judge-v1.0.0 https://github.com/CharanVelavan/ORCA.git ORCA-judge
cd ORCA-judge
python scripts/judge_release_manifest.py --verify docs/releases/judge-v1.0.0.json
```

Use Python 3.12 and `python3`/`py -3.12` where appropriate. `core.autocrlf=false` is local to this clone
and preserves the canonical bytes for source-file checksums; it does not change global Git settings.
Windows working trees with automatic CRLF conversion can have different text-file hashes while
retaining equivalent logical audit chains. Binary PDF/video/weight checksums must match exactly.

Then run `./quickstart.sh` or `.\quickstart.bat`. The default mock dashboard needs no Qwen endpoint.
For live inference, model/KB downloads and performance checks, follow
[the judge guide](../JUDGE_REPRODUCIBILITY.md) and
[the post-submission verification scope](../POST_SUBMISSION_VERIFICATION.md).

The release page attaches the approved report, this manifest and a verification archive containing
recordings and frozen benchmark inputs. It links to the 4K videos. Large model weights, the restored
Chroma database and video production working files remain outside the code release; their published
revisions and checksums are pinned in the manifest. The frozen request archive supports exact input
reconstruction; it does not promise identical inference output on different hardware.
