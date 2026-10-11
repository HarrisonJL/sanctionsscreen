# SanctionsScreen

**Is this counterparty on OFAC's SDN list?** A GenLayer Intelligent Contract that screens a name and/or a crypto address against the US Treasury's Specially Designated Nationals list, **read live from OFAC's own publication service by a committee of validators**, with the matching done by plain code and an LLM that can only *add* suspicion, never remove it. Every verdict records the list's own publication time and the SHA-256 of both files it was made against, and a consumer contract reads it as a freshness-gated yes or no. CounterpartyGate, the consumer here, composes it with [KYB Desk](https://github.com/HarrisonJL/kybdesk): a company is onboarded and paid only if the Companies House register **and** the sanctions screen both say yes, right now.

| | |
|---|---|
| Network | GenLayer Studio Next (chain 61997) |
| SanctionsScreen | [`0x31c89cA668Cf19E1dA583f983d77d4848b25522B`](https://explorer-studio-dev.genlayer.com/address/0x31c89cA668Cf19E1dA583f983d77d4848b25522B) |
| CounterpartyGate (consumer) | [`0x71392Ddc9A39ba977939cbDa8f7b6e5294387498`](https://explorer-studio-dev.genlayer.com/address/0x71392Ddc9A39ba977939cbDa8f7b6e5294387498) |
| Live proof | [CONTRACT.md](CONTRACT.md): fifteen subjects screened against the real list, every verdict path, and the gate allowing and refusing, every transaction linked |
| Tests | 146 Direct Mode tests on the real SDN.CSV and ALT.CSV; 92 safety mutations, all killed (86 on SanctionsScreen, 6 on CounterpartyGate) |

> **A screening aid, not a compliance programme.** It screens against the SDN list only, by the name and address you give it. Sanctions compliance needs human judgement and records of that judgement; this gives a committee-attested, reproducible first pass and refuses to call anything "clear" that it could not fully read. See "What this proves, and what it doesn't".

## Why this exists

A treasury or onboarding contract that pays a counterparty is expected to have screened it. The list is public, changes several times a month, and is about 6.8 MB; deterministic contracts can't read it, and a screening oracle that is simply *trusted* is the weak link. Here every validator downloads the list itself, parses all of it, and must reach the same answer, and the answer says which list it is about.

The matching is the hard part. A name on a list is rarely spelled the way a counterparty writes it (`Kadhafi Muammar` for `QADHAFI, Muammar`; `Mahan Airlines` for `MAHAN AIR`; legal forms, accents, word order, transliteration), and a generic name (`Trading Company Limited`) matches thousands of entries by chance. The design question is what an LLM may be allowed to do in a control like this. The answer here: it may only make a verdict *more* cautious.

## How it decides

### 1. The list is OFAC's, read whole, and fails closed

`screen(subject_id)` makes every validator download `SDN.CSV` (entries) and `ALT.CSV` (aliases) from `sanctionslistservice.ofac.treas.gov`. Any of these is `UNDETERMINED`, never "nothing found": a file that does not answer 200; two files published at different times (their `Last-Modified` headers differ); a list older than 30 days or dated in the future; fewer than 10,000 entries or 5,000 aliases; any row that does not parse (the only permitted odd row is the file's trailing Ctrl-Z); a duplicate or non-numeric entry id; an alias of an entry that does not exist. The list's publication time and the SHA-256 of both files go into the record.

### 2. Plain code decides every positive

| Verdict | Decided by | Meaning |
|---|---|---|
| `ADDRESS_MATCH` | plain code | The address appears in an SDN entry's remarks (`Digital Currency Address - XBT …`). Hex addresses compare case-insensitively; base58 addresses exactly. It wins over everything else: a clean name cannot hide a listed address. |
| `NAME_MATCH` | plain code | The name's *distinctive words* (accents folded, case ignored, legal forms and single letters dropped, in any order) equal those of an SDN name or **alias**. |
| `POSSIBLE_MATCH` | plain code, or the reader | The name shares nearly all its distinctive words with an entry (strong similarity); or the reader judged it plausibly the same party as a resembling entry; or it resembles more entries than a reader can review. |
| `NO_MATCH` | both readers | Plain code found nothing at the strong tier **and** either nothing resembles the name, or a reader reviewed every entry that does and dismissed them all. |
| `UNDETERMINED` | fail closed | The list could not be read completely or recently, the name has no distinctive word (a name made only of `trading`, `bank`, `group`… is never cleared), or the reader's answer could not be read. |

Scoring uses integers only, so every validator computes the same result. A word's weight comes from how many names in the list contain it (or a spelling variant of it): `trading` appears in 809, `mahan` in 5.

### 3. The reader can only escalate

Names that are close but not close enough for plain code to call (a missing word, a transliteration, an abbreviation) are shown to an LLM reader, up to eight entries, with their types, programs and aliases. It answers which, if any, could plausibly be the same party; it is told to be careful rather than confident. It is **never asked** about an address match, a name match or a strong match, and could not clear them if it were (the tests mock a reader that clears everything and confirm it is never called). An answer that names an id it was not shown, or is not JSON, is asked for once more and then makes the verdict `UNDETERMINED`. The subject's name is the one caller-supplied text that reaches the prompt, so names are restricted to letters, digits, spaces and `. , & ' ( ) / -` (no line breaks, quotes or markup) and are framed as untrusted data.

`NO_MATCH` therefore needs two readers to agree there is nothing; a miss needs both to miss.

### 4. The verdict is recomputed, never taken from the leader

The validators must agree exactly on everything plain code derives (the list's date and hashes, every address, name and similarity hit) and on the decision a consumer acts on. The verdict stored is recomputed from the agreed facts and reading.

## Equivalence principle

A custom leader/validator pair (`gl.vm.run_nondet`): exact agreement on the facts (the list's publication time, SHA-256 of both files, row counts, the subject's words, every hit and every entry shown to the reader); on the reading, agreement on the decision (escalate or not), plus the leader's named entries must be ones this validator's own list shows for the subject; and a reading of a subject plain code has already decided is rejected. The consensus-boundary tests show validators rejecting: tampered hashes, dates, counts, hits and reviewed entries; a leader that hides or flips the reading; a reading naming an entry that was not shown; a reading of nothing; malformed readings; and a clean leader when this validator cannot read the aliases.

## CounterpartyGate: two controls, asked again at every payment

`CounterpartyGate` ([`contracts/counterparty_gate.py`](contracts/counterparty_gate.py)), proven live against the real KYB Desk, onboards a UK company and later pays it only if **KYB Desk** approves it (a fresh, unexpired `GOOD_STANDING` check of Companies House) **and** `SanctionsScreen.is_cleared` is true for the subject the owner pairs with it (a fresh `NO_MATCH` against a list that was recent when it was read). Both are asked again at the moment of every payment. A refusal says which control said no and why. The owner pairs a company number with a subject id; the gate cannot tell whether the screened name is the company's, so the pairing is the owner's recorded act.

## What this proves, and what it doesn't

| It proves | It does not prove |
|---|---|
| Which list was read: its publication time and the SHA-256 of both files, agreed by a committee | That the list is **complete or correct**: it is OFAC's SDN list as published |
| An address or name in the subject appears in an SDN entry or alias, with that entry | That the subject **is** the listed party: a `NAME_MATCH` is a name equality, not an identity |
| A committee of validators agreed no entry resembles the subject, or that those which do were reviewed and dismissed | That a subject is **not sanctioned**. `NO_MATCH` means nothing resembling it was found in the list read, on that date |
| That a name too generic to screen was not called clear | Anything about **other lists** (OFAC's non-SDN consolidated lists, UK, EU, UN), **ownership** (the 50% rule), or **jurisdiction** |
| | Anything about an address's **cluster or counterparties**: only addresses OFAC lists are matched |

## Known limitations

- **OFAC SDN only.** `SDN.CSV` and `ALT.CSV`. The UK OFSI and EU lists are 16 MB each and were not attempted (research/README.md); OFAC's non-SDN consolidated lists are not included.
- **Names are matched by words.** Transliterations are reached by spelling variants of *long* words (a skeleton of consonants, or one letter apart) and shown to the reader, not decided by plain code. A short word spelled differently (`Ahmad`/`Ahmed`) is only caught through the other words of the name.
- **A name with no distinctive word cannot be screened.** `Trading Company Limited` is `UNDETERMINED`, on purpose. So is a name where every word is common. Screen the full legal name, or the address.
- **More than eight resembling entries is a `POSSIBLE_MATCH`**, not a judgement: a subject sharing a distinctive word with 19 sanctioned entities (`Sberbank Group`) needs a person.
- **The reader is an LLM.** It can only escalate, and it is shown the candidates plain code nominated; a model can still wrongly dismiss a resembling entry. Plain code's strong tier, exact names and addresses do not depend on it.
- **Freshness is the consumer's rule.** A verdict is a record of one moment; `is_cleared(subject, max_age_seconds, max_list_age_days)` makes the consumer say how recent it must be.
- **Subject ids are first-come and immutable.** Someone can register an id before you; read `get_subject` and pin what you expect.
- **The OFAC service is one source.** If it is down or blocks validators, screening is `UNDETERMINED`, not skipped.
- **Studio Next only.**

## Running it

```bash
python3 -m venv .venv && .venv/bin/pip install genlayer-test==0.29.2 genvm-linter==0.11.0 pytest
.venv/bin/pytest tests -q                     # 146 tests (parses the real 6.8 MB list)
.venv/bin/genvm-lint check contracts/sanctions_screen.py
python3 scripts/mutation_check.py             # every safety mutation must be killed
python3 scripts/capture_fixtures.py           # re-capture the real OFAC files

cd studio-next && npm ci
npx tsx check_schema.ts sanctions_screen_studio_next.py
npx tsx verify_code.ts <address> sanctions_screen_studio_next.py    # on-chain code == this repo
```

## Repository layout

```
contracts/sanctions_screen.py              tested source (GenVM v0.2.11)
contracts/sanctions_screen_studio_next.py  deployed port (Studio Next)
contracts/counterparty_gate*.py            consumer contract + port
tests/                                     Direct Mode tests, the real OFAC files (gzipped), mutations*.txt
scripts/                                   fixture capture, port, mutation check
studio-next/                               deploy, schema check, live proof (prove.ts, live_proof.json), verify_code.ts
research/                                  what GenVM can read and compute, and the probe contract
```
