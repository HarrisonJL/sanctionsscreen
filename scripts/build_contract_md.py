"""
Writes CONTRACT.md from studio-next/live_proof.json (the log prove.ts wrote as it ran), so no transaction
hash or verdict in it is ever transcribed by hand.   python3 scripts/build_contract_md.py
Deployment facts come from studio-next/deployment.json (written by hand once, from the deploy logs).
"""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
L = json.loads((REPO / "studio-next" / "live_proof.json").read_text())
D = json.loads((REPO / "studio-next" / "deployment.json").read_text())
MANIFEST = json.loads((REPO / "tests" / "fixtures" / "manifest.json").read_text())["fixtures"]
X = "https://explorer-studio-dev.genlayer.com"


def tx(h): return f"[`{h[:10]}…`]({X}/tx/{h})"
def votes(v):
    a, d = v.count("AGREE"), v.count("DISAGREE")
    return f"{a} agree" + (f", {d} disagree" if d else "")


regs = [e for e in L if e["step"] == "register"]
refs = [e for e in L if e["step"] == "refuse"]
scrs = [e for e in L if e["step"] == "screen"]
gate = [e for e in L if e["step"] in ("gate", "kyb")]
read = next(e for e in L if e["step"] == "read")
assert all(e["result"] in ("FINISHED_WITH_RETURN", "FINISHED_WITH_ERROR") for e in L if "result" in e)
assert not any(v == "DISAGREE" for e in L for v in e.get("votes", [])), "a disagreement belongs in the text"
decided = [e for e in L if "tx" in e]

o = []
w = o.append
w("# SanctionsScreen: deployment and live proof\n")
w("## Deployment\n")
w("| | |\n|---|---|")
w("| Network | GenLayer Studio Next, chain 61997 (`chains.studioDevnet`, genlayer-js 2.0.0-rc.1) |")
w(f"| SanctionsScreen | [`{D['screen']['address']}`]({X}/address/{D['screen']['address']}) - deploy tx {tx(D['screen']['deploy_tx'])} |")
w(f"| CounterpartyGate | [`{D['gate']['address']}`]({X}/address/{D['gate']['address']}) - deploy tx {tx(D['gate']['deploy_tx'])}; constructed with KYB Desk `{D['gate']['kyb']}`, SanctionsScreen's address, `max_age_seconds` 86400 and `max_list_age_days` 30 |")
w("| Runner | `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng` (v0.3.0) |")
w("| Deployer | `0x5cdb5699bc1038e115A973bb91A646f7E98C075b` |\n")
w("Both contracts passed the live runner's `getContractSchemaForCode` check before deploying, and **the code on-chain is byte-identical to this repo**: `cd studio-next && npx tsx verify_code.ts <address> <file>` fetches it with `gen_getContractCode` and compares.\n")
w("| Contract | SHA-256 on-chain = SHA-256 of the repo file |\n|---|---|")
w(f"| SanctionsScreen / `contracts/sanctions_screen_studio_next.py` | `{D['screen']['sha256']}` |")
w(f"| CounterpartyGate / `contracts/counterparty_gate_studio_next.py` | `{D['gate']['sha256']}` |\n")
w(f"## Live proof ({D['date']})\n")
w(f"Reproduce with `cd studio-next && npx tsx prove.ts <sanctionsscreen> <counterpartygate> <register|screen|gate|read>`. Every row is from [`studio-next/live_proof.json`](studio-next/live_proof.json), written as it ran (it resumes where it stopped), with the contract's recorded output. \"Agree\" counts the validators that actively voted (Studio Next leaves the rest of the 5-seat committee idle). **All {len(decided)} transactions reached consensus with every voting validator agreeing**, including the ones the contracts refused: a refusal is a decided outcome.\n")
first = next(e for e in scrs if e["check"])["check"]
w(f"Every screening below was made against **the OFAC list published {first['list_published']}**: `SDN.CSV` ({first['facts']['sdn_rows']:,} entries, SHA-256 `{first['facts']['sdn_sha256']}`) and `ALT.CSV` ({first['facts']['alt_rows']:,} aliases, SHA-256 `{first['facts']['alt_sha256']}`). Those are the hashes of the files committed gzipped in `tests/fixtures/`, and the tests replay every screening on them.\n")

w("### Screening subjects against the real list\n")
w("| Subject | What it shows | Verdict | Behind it | Tx |\n|---|---|---|---|---|")
for e in scrs:
    c = e["check"]
    subject = " + ".join(x for x in (f"`{e['name']}`" if e["name"] else "", f"address `{e['address'][:14]}…`" if e["address"] else "") if x)
    behind = "; ".join(f"{m['name']} (#{m['ent_num']}, via {m['via']})" for m in c["matches"][:2]) or (c["reasons"][0] if c["reasons"] else "")
    if c["reading"] is not None:
        behind += f" · reader: {'escalated ' + ', '.join(c['reading']['possible']) if c['reading']['possible'] else 'dismissed ' + str(len(c['facts']['review'])) + ' resembling'}"
    w(f"| {subject} | {e['note']} | **{c['verdict']}** | {behind} | {tx(e['tx'])} {votes(e['votes'])} |")
w("\nThe reader's answers are the validators' own LLMs on Studio Next. The deterministic rows (`ADDRESS_MATCH`, `NAME_MATCH`, the strong `POSSIBLE_MATCH`, the generic `UNDETERMINED`, the plain `NO_MATCH`) never reach it.\n")

w("### Registrations the contract refuses\n")
w("| What it tries | Tx | Revert message |\n|---|---|---|")
for e in refs:
    w(f"| {e['note']} | {tx(e['tx'])} {votes(e['votes'])} | `{e['revert']}` |")

w("\n### CounterpartyGate: two controls, asked again at every payment\n")
w("The gate is pointed at the real KYB Desk (the contract behind kybdesk.vercel.app). The gate wants a KYB approval no older than a day, so the proof first asks KYB Desk for fresh checks of the companies it onboards (rows marked KYB).\n")
w("| Step | Call | Outcome | Tx |\n|---|---|---|---|")
for e in gate:
    if e["step"] == "kyb":
        a = e["approval"]
        w(f"| {e['note']} | `KYBDesk.attest({e['args'][0]})` | approval now: **{a['reason']}** | {tx(e['tx'])} {votes(e['votes'])} |")
    else:
        out_ = "**allowed**" if e["result"] == "FINISHED_WITH_RETURN" else f"refused: `{e['revert']}`"
        w(f"| {e['note']} | `{e['call']}({', '.join(str(a) for a in e['args'])})` | {out_} | {tx(e['tx'])} {votes(e['votes'])} |")
cfg = read["gate_config"]
w(f"\nAfter the run `CounterpartyGate.get_config()` reports {cfg['counterparty_count']} counterparties onboarded and {cfg['payment_count']} payments made; `SanctionsScreen.is_cleared(subject, 86400, 30)` is true for: " + ", ".join(f"`{k}`" for k, v in read["is_cleared"].items() if v) + ".\n")

w("## What the live run found\n")
for t in D.get("found_live", []):
    w("- " + t)
w("")
if D.get("superseded"):
    w("## Superseded deployments\n")
    w("| Contract | Address | Why it is superseded |\n|---|---|---|")
    for s in D["superseded"]:
        w(f"| {s['contract']} | `{s['address']}` | {s['why']} |")
    w("")
w("## Proven in tests, not live\n")
w("Direct Mode proves these on the real list (or the real list with one marked field changed); none has a live transaction:\n")
w("- Every way a list can fail to parse (truncated, a stray column, a duplicate or non-numeric id, an alias of an unknown entry, a bare carriage return), a list published at two times, a missing or unreadable `Last-Modified`, a list older than 30 days, exactly 30 days old, or dated in the future.")
w("- The reader refusing to be asked for what plain code decided, and a reader whose answer is not JSON, names an entry it was not shown, or raises.")
w("- The validators' consensus boundary: tampered facts, a leader that hides or flips the reading, a reading of nothing, malformed readings.")
w("- Every CounterpartyGate check that runs before its cross-contract calls (owner, amount, constructor limits, paying a company never onboarded). Its checks that read KYB Desk and SanctionsScreen, and the refusal to onboard a company twice, are proven by the live table above, because Direct Mode cannot simulate a cross-contract call or a first successful onboard. A *stale* approval or screening has no live refusal (it would need a day to pass).")
w("- The replay: `test_the_fixtures_reproduce_what_the_validators_agreed_on_live` runs every live screening again on the committed OFAC files and requires the same facts (down to the file hashes), verdict, reasons and matches.")
(REPO / "CONTRACT.md").write_text("\n".join(o) + "\n")
print("wrote CONTRACT.md,", len(o), "lines;", len(decided), "transactions")
