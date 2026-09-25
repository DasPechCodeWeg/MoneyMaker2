# py315ready

**Find out whether your Python dependencies will install on Python 3.15 before your CI finds out for you.**

`py315ready` reads a `requirements.txt` file or a list of package names. It asks PyPI what the latest release of each package actually ships, and puts each package in one of these groups:

| Status | Meaning |
| --- | --- |
| `READY` | A wheel that installs on CPython 3.15 exists: pure-Python, `cp315`/`cp315t`, or stable-ABI `abi3` |
| `NO-WHEEL` | Binary wheels exist for older Pythons but none for 3.15. `pip` falls back to compiling from source, which needs a toolchain, slows CI and often fails |
| `SDIST-ONLY` | No wheels at all, only a source archive |
| `BLOCKED` | The package's `Requires-Python` excludes 3.15 |
| `ERROR` | The package was not found on PyPI, or a network error occurred |

A live run on 65 widely used compiled packages found **18 without an installable 3.15 wheel**, among them `torch`, `tensorflow`, `pyarrow`, `aiohttp`, `pyyaml`, `markupsafe`, `duckdb` and `numba`. See [SAMPLE_REPORT.md](SAMPLE_REPORT.md), which you can regenerate yourself with the command in its header.

## Use it (free, MIT)

It needs only the Python standard library, with no install and no token:

```bash
curl -O https://raw.githubusercontent.com/DasPechCodeWeg/MoneyMaker2/HEAD/py315ready.py
python3 py315ready.py -r requirements.txt           # Markdown table
python3 py315ready.py -r requirements.txt --format json
python3 py315ready.py numpy torch pyyaml            # ad-hoc names
```

The exit code is `1` when anything is `BLOCKED` or `NO-WHEEL`, so it can gate CI. Pass `--lenient` to fail only on `BLOCKED`.

As a GitHub Action:

```yaml
- uses: DasPechCodeWeg/MoneyMaker2@opus-m3/py315ready
  with:
    requirements: requirements.txt
```

It has limits. It checks the latest *final* release on PyPI, not pre-releases, private indexes or your pinned versions. A `READY` status means an installable file exists, not that your code passes its tests on 3.15.

## Paid help: you pay only after delivery

If the report shows a red row and you would rather not spend the afternoon on it:

| Service | Price | What you get |
| --- | --- | --- |
| **Upgrade audit** | **USD 29** one-time | We run the check against your requirements or lock file (up to 150 packages). For every `NO-WHEEL`, `SDIST-ONLY` or `BLOCKED` package you get the concrete way out: a version pin, the upstream issue or PR that tracks 3.15 wheels, a drop-in alternative, or the build flags and system packages the source build needs. Delivered as a Markdown file within 2 business days. |
| **Unblock PR** | **USD 149** one-time | A pull request to **your own** repository that makes it pass on Python 3.15. It adds 3.15 to the CI matrix and fixes what breaks. For projects that ship extensions, it also includes a `cibuildwheel` config that builds `cp315` and `cp315t` wheels. You get CI logs as evidence. |
| **Watch** | **USD 9** per month | Up to 5 requirements files are re-checked weekly. An issue is opened in a repository you choose when something changes. |

**How ordering works:**
1. Open an issue with the **"Order"** form in this repository. You can link a public repo or paste the requirements. Do not paste secrets.
2. You receive the deliverable in that issue, or as a PR to your repo.
3. If you are satisfied, pay through [GitHub Sponsors](https://github.com/sponsors/DasPechCodeWeg) as a one-time sponsorship of the matching tier. If you are not satisfied, you pay nothing.

**Disclosure:** deliverables are produced with an AI coding agent. Every claim in a deliverable comes with its evidence, such as a PyPI file listing, an upstream link or a CI log, so you can verify it before paying. We only open PRs on repositories whose owner ordered one.

## Development

```bash
python3 -m unittest -v test_py315ready
```

MIT licensed.
