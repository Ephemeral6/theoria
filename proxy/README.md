# `/proxy/` — the double proxy

Phase 1's record surface. Two HTTP proxies stand between an arm and the outside
world, and between them they turn "the system is closed" from a discipline the
arms are asked to keep into a property of the construction.

```
        arm process (holds no credential)
             |                    |
   ARC_BASE_URL          MODEL_BASE_URL
             |                    |
      env_proxy  <-- keys --> model_proxy
             |                    |
      three.arcprize.org   api.anthropic.com
             \                    /
              \                  /
                  ledger.jsonl
```

"Closed" was given three properties, and each one has something here that makes
it checkable rather than asserted:

| Property | What makes it true | What checks it |
|---|---|---|
| **Complete record** | both proxies write every request and response | `LEDGER_FORMAT.md`, `ledger.py` |
| **Replayable** | frames are stored whole and hashed | `replay.py` — replays the actions, compares hashes step by step |
| **No bypass** | the arm holds neither key | `tests/test_seal.py` — the bypass is attempted and fails |

Plus the obligation Phase 1 attaches to the ledger: the score derived from
`env_step` records **must** equal the API scorecard's score (`reconcile.py`),
and inequality is an incident, not a diagnostic.

## Run it

Nothing below spends a dollar or opens a socket to the internet.

```bash
cd proxy && python -m pytest              # 70 tests
cd .. && python -m proxy.runner --mock    # one full game through both proxies
python -m proxy.replay    --run-id <run> --mock   # re-run it; compare frame hashes
python -m proxy.reconcile --run-id <run>          # ledger score vs scorecard score
python -m proxy.cost                              # usage x a versioned price table
```

Against the live API, drop `--mock` and give `--game`. The credential is read
from the gitignored `.env` **inside the proxy** and never reaches the arm:

```bash
python -m proxy.runner --game ar25-0c556536 --arm theoria
```

To put an existing arm behind the proxies without touching its code, run them
standalone and set two environment variables:

```bash
python -m proxy.env_proxy   --port 8711 --arm bare_cc --run-id r-001 &
python -m proxy.model_proxy --port 8712 --arm bare_cc --run-id r-001 &
ARC_BASE_URL=http://127.0.0.1:8711 MODEL_BASE_URL=http://127.0.0.1:8712 <arm>
```

## Layout

| File | What it is |
|---|---|
| `LEDGER_FORMAT.md` | **normative**, written before the code. Two event shapes, `env_step` and `model_call`. The format three arms and the Phase 2 metric battery share. |
| `ledger.py` | its executable form. Append-only by construction — no update, rewrite or delete path exists. |
| `guard.py` | the sealed-pile guard, sourced from `arc-recon/data/piles.json` and integrity-checked against the digest the cut recorded |
| `env_proxy.py` | the arm's only route to the environment; injects `ARC_API_KEY`, records, enforces the guard, applies variants |
| `model_proxy.py` | the arm's only route to a provider; records the usage block verbatim |
| `variants.py`, `variants/` | the wrapper-legal operator set, and four specs each carrying a constructive justification |
| `replay.py` | replays a run from the ledger; a **probe scorecard** keeps the original game's counts clean |
| `reconcile.py` | the score obligation, plus a recompute of the derived `level` fields |
| `cost.py`, `pricing/` | cost as a conversion over a versioned price table. No dollar figure is ever written to the ledger. |
| `runner.py` | orchestrates one game: one run, one scorecard, one shared step counter |
| `mock/` | a deterministic stand-in environment, a stand-in provider, and a keyless arm |

## The variant layer

We do not rewrite games. The environment is hosted, so a wrapper provably
cannot touch the server's internal dynamics — and a variant whose truth we
could not state would be worse than no variant. The operator library is
therefore the **wrapper-legal set** and nothing else:

`forbid_action` · `remap_action` · `step_limit` · `observation_loss` · `win_tighten`

Every spec must carry a **constructive justification** — why the claim follows
from the construction, not from having run it. `Variant.load` refuses a spec
without one, and refuses an operator outside the legal set. The four shipped
specs are three unsolvable and one solvable; an exam made only of unsolvable
questions cannot tell "I failed" apart from "it was impossible".

## Two things worth knowing before building on this

* **Streaming is buffered, not passed through live.** The model proxy reads a
  streamed response to completion before answering the arm, so it can record
  it. Usage and content are captured correctly (`tests/test_e2e.py` checks the
  `message_start` / `message_delta` merge), but an arm that renders tokens as
  they arrive will see them arrive all at once. Nothing in Phase 1 needs
  incremental delivery; an arm that does will need this changed.
* **The mock world is not ARC.** It is deterministic, has three levels, and
  returns several frames from one command — the properties the harness has to
  handle. It says nothing about how the real games behave. `precheck.json`
  already registers `g50t-5849a774` as non-deterministic, so the first live run
  through these proxies should expect a replay failure to mean *the world*, not
  the harness, until proven otherwise.
