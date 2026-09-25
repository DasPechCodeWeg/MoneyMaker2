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

A live run on 2026-09-25 against 65 widely used compiled packages found **18 without an installable 3.15 wheel**, among them `torch`, `tensorflow`, `pyarrow`, `aiohttp`, `pyyaml`, `markupsafe`, `duckdb` and `numba`. See [SAMPLE_REPORT.md](SAMPLE_REPORT.md), which you can regenerate yourself with the command in its header.

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

**Who delivers:** the holder of this GitHub account, `DasPechCodeWeg`. That is one person, not a company or a team. The work is done with an AI coding agent (Claude).

| Service | Price | What you get |
| --- | --- | --- |
| **Upgrade audit** | **USD 29** | For a requirements or lock file you post (up to 150 packages): the py315ready table, plus the evidence and one concrete option for each package that is not `READY`. The option is a version pin, the upstream issue or PR tracking 3.15 wheels, an alternative package, or what a source build needs. It is posted as a comment in your issue. |
| **Unblock PR** | **USD 149** | For a **public** repository **you own**: a pull request that adds Python 3.15 to CI and tries to fix what breaks. For projects with compiled extensions, it also adds a `cibuildwheel` configuration for `cp315` and `cp315t` wheels. If CI does not pass on 3.15, you owe nothing. |

**How an order works:**
1. Open an issue in this repository using the **Order** form.
2. The account holder replies in that issue to **accept or decline**. Nothing is binding before that reply, no work starts before it, and the reply states the delivery date. If nobody replies, there is no order and you owe nothing.
3. The audit is delivered in the issue. The unblock work is delivered as a PR to your repository.
4. The delivery comment says how to pay. You pay **only if you are satisfied**, and you never pay in advance.

**What this is not:**
- It is no guarantee that upstream projects will publish 3.15 wheels.
- There is no work on repositories you do not own, and no private repositories.
- We never ask for your tokens or secrets.

Every claim in a deliverable links to its evidence, such as a PyPI file listing, an upstream issue or a CI log, so you can check it before paying.

## Development

```bash
python3 -m unittest -v test_py315ready
```

MIT licensed.
