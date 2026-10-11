# SanctionsScreen: deployment and live proof

## Deployment

| | |
|---|---|
| Network | GenLayer Studio Next, chain 61997 (`chains.studioDevnet`, genlayer-js 2.0.0-rc.1) |
| SanctionsScreen | [`0x31c89cA668Cf19E1dA583f983d77d4848b25522B`](https://explorer-studio-dev.genlayer.com/address/0x31c89cA668Cf19E1dA583f983d77d4848b25522B) - deploy tx [`0xa4552b28…`](https://explorer-studio-dev.genlayer.com/tx/0xa4552b28e49c21952c545878e5f16d4d0474b8bc9302fef8c16bed268ce0da4e) |
| CounterpartyGate | [`0x71392Ddc9A39ba977939cbDa8f7b6e5294387498`](https://explorer-studio-dev.genlayer.com/address/0x71392Ddc9A39ba977939cbDa8f7b6e5294387498) - deploy tx [`0xed50c324…`](https://explorer-studio-dev.genlayer.com/tx/0xed50c3243ba8be3aca9f8e9759b7dc1f771d241ec6038b2410530121041b67f9); constructed with KYB Desk `0x962Ee34181C4981Be098527a4B2d8Fe0Ba31D8fB`, SanctionsScreen's address, `max_age_seconds` 86400 and `max_list_age_days` 30 |
| Runner | `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng` (v0.3.0) |
| Deployer | `0x5cdb5699bc1038e115A973bb91A646f7E98C075b` |

Both contracts passed the live runner's `getContractSchemaForCode` check before deploying, and **the code on-chain is byte-identical to this repo**: `cd studio-next && npx tsx verify_code.ts <address> <file>` fetches it with `gen_getContractCode` and compares.

| Contract | SHA-256 on-chain = SHA-256 of the repo file |
|---|---|
| SanctionsScreen / `contracts/sanctions_screen_studio_next.py` | `c88f39d117a4ed448fc6c2ca8f464bde3aa34a35b92ebad60e9604d77b8b485c` |
| CounterpartyGate / `contracts/counterparty_gate_studio_next.py` | `5af804c07e291399ccdeceea22fd8233c5f8516b8c7466a554d1a003d7594860` |

## Live proof (2026-10-11)

Reproduce with `cd studio-next && npx tsx prove.ts <sanctionsscreen> <counterpartygate> <register|screen|gate|read>`. Every row is from [`studio-next/live_proof.json`](studio-next/live_proof.json), written as it ran (it resumes where it stopped), with the contract's recorded output. "Agree" counts the validators that actively voted (Studio Next leaves the rest of the 5-seat committee idle). **All 50 transactions reached consensus with every voting validator agreeing**, including the ones the contracts refused: a refusal is a decided outcome.

Every screening below was made against **the OFAC list published 2026-10-09T14:01:35Z**: `SDN.CSV` (19,416 entries, SHA-256 `64be7a7991059f59a2ebb43bc5dcc7e2951e1e27cbed8cbe41b0231b3a161946`) and `ALT.CSV` (20,182 aliases, SHA-256 `ff6075fc9635c5034475fa49c0c2e0e03300e1c9375771d75f99c4d4bf799c1b`). Those are the hashes of the files committed gzipped in `tests/fixtures/`, and the tests replay every screening on them.

### Screening subjects against the real list

| Subject | What it shows | Verdict | Behind it | Tx |
|---|---|---|---|---|
| `Aerocaribbean Airlines Ltd` | an SDN entry, written with a legal form | **NAME_MATCH** | AEROCARIBBEAN AIRLINES (#36, via name) | [`0x7c1dc3d5…`](https://explorer-studio-dev.genlayer.com/tx/0x7c1dc3d511ef262a3fb86667ae993f1f5a8cc2e3067e5bdb7c1e17271e2f3478) 3 agree |
| `Aero-Caribbean` | an alias OFAC lists for that entry | **NAME_MATCH** | AEROCARIBBEAN AIRLINES (#36, via name) | [`0xb7d1a2e3…`](https://explorer-studio-dev.genlayer.com/tx/0xb7d1a2e353729ea50800ef5c131dca563a0d2f5d490ede1f9eb0ab2e61057bca) 3 agree |
| `Tesco PLC` + address `TNiq9AXBp9EjUq…` | a clean name carrying a Tron address from Bank Markazi's SDN remarks | **ADDRESS_MATCH** | BANK MARKAZI JOMHOURI ISLAMI IRAN (#4632, via address) | [`0x09f1c580…`](https://explorer-studio-dev.genlayer.com/tx/0x09f1c58002a634083c08e3a23a7dfe0e067df70e7a257131d970f024ca6747a1) 3 agree |
| address `44dZUJ7w1T3fKA…` | an address alone: a Monero address of ISIL-Khorasan | **ADDRESS_MATCH** | ISIL KHORASAN (#18647, via address) | [`0x2961bfef…`](https://explorer-studio-dev.genlayer.com/tx/0x2961bfef413f313df5b2bdd2213780dfd2df86e6125d19184c2ceb9ef02029e7) 3 agree |
| address `0x983a81ca6FB1…` | an Ethereum-format address, checksummed, of Valerian Labs | **ADDRESS_MATCH** | VALERIAN LABS, INC. (#45314, via address); VALERIAN LABS, INC. (#45314, via address) | [`0xf4f9fbdd…`](https://explorer-studio-dev.genlayer.com/tx/0xf4f9fbdd7fad531ee8ea7ebcae04ef3d15ae8553bcfdda455a03481442937353) 3 agree |
| `Bank Markazi Jomhouri Islami` | the entry minus its last word: a strong possible match, no reader | **POSSIBLE_MATCH** | BANK MARKAZI JOMHOURI ISLAMI IRAN (#4632, via similar) | [`0xc098b56c…`](https://explorer-studio-dev.genlayer.com/tx/0xc098b56cc6ba41178e6734c383fc835fa8b8cdc06a6bef4c2995d2c72164d8c1) 3 agree |
| `Mahan Airlines` | a missing word (the entry is MAHAN AIR): the reader escalates | **POSSIBLE_MATCH** | MAHAN AIR (#12927, via review) · reader: escalated 12927 | [`0xe08f3c48…`](https://explorer-studio-dev.genlayer.com/tx/0xe08f3c48e49dc36b859c9e5d83f1fb93be03f7d39ef95a022013b9a05aec9443) 3 agree |
| `Kadhafi Muammar` | a transliteration (QADHAFI, Muammar): the reader escalates | **POSSIBLE_MATCH** | QADHAFI, Muammar (#12606, via review) · reader: escalated 12606 | [`0x6c57451d…`](https://explorer-studio-dev.genlayer.com/tx/0x6c57451dfb8b10d6cddb00b36d1ccb97e5569c5eeb05d6321c2ea2b2c54b5423) 3 agree |
| `Sberbank Group` | resembles 19 entries, more than a reader can review | **POSSIBLE_MATCH** | PUBLIC JOINT STOCK COMPANY SBERBANK OF RUSSIA (#17018, via review); LIMITED LIABILITY COMPANY SBERBANK CAPITAL (#18669, via review) | [`0x770c6705…`](https://explorer-studio-dev.genlayer.com/tx/0x770c67051420386d918adf6f8c64048ba251deb01bacb94d219d3c948d5c9f4d) 3 agree |
| `Tesco PLC` | resembles nothing: no match, decided by plain code | **NO_MATCH** |  | [`0xa6e87d40…`](https://explorer-studio-dev.genlayer.com/tx/0xa6e87d408d14d59acce63d6b13e6aed407231945d4f2fb9afdc65cbe164fd17e) 3 agree |
| `J Sainsbury plc` | resembles nothing: no match | **NO_MATCH** |  | [`0xd37cd435…`](https://explorer-studio-dev.genlayer.com/tx/0xd37cd435d390c48b3efbb0c5b3ba06e15b5699a34354a8f4e47ad56cd4053d1c) 3 agree |
| `Peninsula Storage Solutions Ltd` | resembles nothing: no match | **NO_MATCH** |  | [`0xe74f8360…`](https://explorer-studio-dev.genlayer.com/tx/0xe74f83607c6d4840d066217efdb01153fe208ba466de9a9e1c0d090aa6023fe3) 3 agree |
| `Apple Inc` | resembles one entry; the reader dismisses it | **NO_MATCH** | 1 resembling entries reviewed and dismissed · reader: dismissed 1 resembling | [`0x21501599…`](https://explorer-studio-dev.genlayer.com/tx/0x215015996a6fc0f0939c22ca42a3e9959a96a89bbf429aff5bf1c586207993c7) 3 agree |
| `Banco Santander SA` | resembles a few entries; the reader dismisses them | **NO_MATCH** | 2 resembling entries reviewed and dismissed · reader: dismissed 2 resembling | [`0xc2171950…`](https://explorer-studio-dev.genlayer.com/tx/0xc21719509a0988235ce3e99451bc8e9eae86bb6be646532f2954f467050afa53) 3 agree |
| `Trading Company Limited` | no distinctive word: never cleared | **UNDETERMINED** | name_too_generic_to_screen | [`0x30e6857d…`](https://explorer-studio-dev.genlayer.com/tx/0x30e6857d8d78ee1870f6907ef1d6fbc4614b7acdc2e725ce7d926f9b1e2b5ff3) 3 agree |

The reader's answers are the validators' own LLMs on Studio Next. The deterministic rows (`ADDRESS_MATCH`, `NAME_MATCH`, the strong `POSSIBLE_MATCH`, the generic `UNDETERMINED`, the plain `NO_MATCH`) never reach it.

### Registrations the contract refuses

| What it tries | Tx | Revert message |
|---|---|---|
| a subject id used twice | [`0xe792c108…`](https://explorer-studio-dev.genlayer.com/tx/0xe792c1080c2e4615d8972d43f045ce5f5e7d4ebf1cfb7537fd90e3430a57fc5c) 3 agree | `subject_id already registered` |
| a name carrying a line break (text that would reach the reader) | [`0x7a2de8b3…`](https://explorer-studio-dev.genlayer.com/tx/0x7a2de8b32b902684b795ea3200e0fb62e3e80382fd16bfabf4abf4a5c3a0c9ab) 3 agree | `name must be 2-200 characters of letters, digits, spaces and . , & ' ( ) / -` |
| a name with no distinctive word | [`0x0dd83279…`](https://explorer-studio-dev.genlayer.com/tx/0x0dd83279611dd30e4cff9bc90e8abbe99609b44926dc378d0eeea65a28b771e5) 3 agree | `name must contain a distinctive word of at least three letters` |
| neither a name nor an address | [`0x142d6b8c…`](https://explorer-studio-dev.genlayer.com/tx/0x142d6b8c1d32aa340aa43662fef001cf7bf0ad6f0ab212f7a020840d585c664e) 3 agree | `give a name, an address, or both` |
| something that is not a crypto address | [`0x6957935b…`](https://explorer-studio-dev.genlayer.com/tx/0x6957935bd2c82a237ec153e66bd334313d25c1c0cb02409653806acb0c66c473) 3 agree | `address must be 20-100 letters and digits (a crypto address)` |

### CounterpartyGate: two controls, asked again at every payment

The gate is pointed at the real KYB Desk (the contract behind kybdesk.vercel.app). The gate wants a KYB approval no older than a day, so the proof first asks KYB Desk for fresh checks of the companies it onboards (rows marked KYB).

| Step | Call | Outcome | Tx |
|---|---|---|---|
| KYB Desk re-checks Tesco PLC (the gate wants an approval no older than a day) | `KYBDesk.attest(00445790)` | approval now: **APPROVED** | [`0x69d9ecca…`](https://explorer-studio-dev.genlayer.com/tx/0x69d9eccaf418c13097a1e25e4642c9ddb19ca979fb5678cf72504aa107efe344) 3 agree |
| KYB Desk re-checks J Sainsbury plc | `KYBDesk.attest(00185647)` | approval now: **APPROVED** | [`0xa0b31016…`](https://explorer-studio-dev.genlayer.com/tx/0xa0b3101607def2d4c903b942aabb6d30862971004d345470a3878be001cdfdc7) 3 agree |
| KYB Desk re-checks Peninsula Storage Solutions | `KYBDesk.attest(14813324)` | approval now: **APPROVED** | [`0x59a9c31a…`](https://explorer-studio-dev.genlayer.com/tx/0x59a9c31abca7c76b1f32afad1f71f905eed6563fa6331e2cbc76104620e7868f) 3 agree |
| approved by KYB Desk and cleared by SanctionsScreen: allowed | `onboard(00445790, tesco)` | **allowed** | [`0x16d55173…`](https://explorer-studio-dev.genlayer.com/tx/0x16d5517395c853bd82d55aa00e3c9cb7f46176765a236ab7b0d690a426fda8b3) 3 agree |
| approved and cleared: allowed | `onboard(00185647, sainsbury)` | **allowed** | [`0x86a58933…`](https://explorer-studio-dev.genlayer.com/tx/0x86a58933c779d0d65610929dd447bec5c90be4f5faa865919e93bcaa5802967a) 3 agree |
| KYB approves, but the subject paired with it is a NAME_MATCH: refused | `onboard(14813324, aerocaribbean)` | refused: `'14813324' refused: SanctionsScreen says NAME_MATCH for 'aerocaribbean', not a fresh NO_MATCH against a recent list` | [`0x8ba5ad38…`](https://explorer-studio-dev.genlayer.com/tx/0x8ba5ad3806c94ced9430121f7ae8f7a6bba89a801a4b56021969a3b33e4d191b) 3 agree |
| KYB approves, the name is clean, the address is listed: refused | `onboard(14813324, markazi-address)` | refused: `'14813324' refused: SanctionsScreen says ADDRESS_MATCH for 'markazi-address', not a fresh NO_MATCH against a recent list` | [`0xad343b12…`](https://explorer-studio-dev.genlayer.com/tx/0xad343b12b950164b80f81ba9f9d21d704e75405226e16f54d3ecd9ca2d842f16) 3 agree |
| KYB approves, but the subject is a POSSIBLE_MATCH: refused | `onboard(14813324, mahan)` | refused: `'14813324' refused: SanctionsScreen says POSSIBLE_MATCH for 'mahan', not a fresh NO_MATCH against a recent list` | [`0xec37d213…`](https://explorer-studio-dev.genlayer.com/tx/0xec37d21334372490488117a44f8940bec0eeaa4f5823cd9b3e78b5d59ce7da9e) 3 agree |
| KYB approves, but the subject cannot be screened (UNDETERMINED): refused | `onboard(14813324, generic)` | refused: `'14813324' refused: SanctionsScreen says UNDETERMINED for 'generic', not a fresh NO_MATCH against a recent list` | [`0xe647b8a9…`](https://explorer-studio-dev.genlayer.com/tx/0xe647b8a937dac797a82d33b2f870d1b4ee162c9e98d1eb81152bdf4f2b70a31a) 3 agree |
| the sanctions subject is clean, but KYB Desk does not approve Thomas Cook Group: refused | `onboard(06091951, tesco)` | refused: `'06091951' refused: KYB Desk says VERDICT_NOT_IN_GOOD_STANDING` | [`0x4174e674…`](https://explorer-studio-dev.genlayer.com/tx/0x4174e67463f7f44f634c005baeb45ac396a71092972fc7757e5720d7e7b0e439) 3 agree |
| the same company with a clean, screened subject: allowed | `onboard(14813324, peninsula)` | **allowed** | [`0x6fef85ae…`](https://explorer-studio-dev.genlayer.com/tx/0x6fef85ae9c06b7b00e946e6c3ea83b6338fc29dacd1f8fc329bb3c9ec8e76cb0) 3 agree |
| a payment: both controls are asked again, now | `pay(00445790, 1500000)` | **allowed** | [`0xceed916c…`](https://explorer-studio-dev.genlayer.com/tx/0xceed916c77c0ccb84dd542ba2cad2abcaf305635a7394c4a5f0ccca5c2437f0e) 3 agree |
| a payment to the second counterparty | `pay(00185647, 2500000)` | **allowed** | [`0xef50976b…`](https://explorer-studio-dev.genlayer.com/tx/0xef50976bf27f658a6ef82c1088bf3b3944807f9e4e373b03e224987a12984b47) 3 agree |
| a company that was never onboarded: refused | `pay(06091951, 100)` | refused: `'06091951' is not onboarded` | [`0x459d76e3…`](https://explorer-studio-dev.genlayer.com/tx/0x459d76e31dd9c735934684993cafb4e0ca62c23e5d0e75c9574f7a80461745cf) 3 agree |
| a company that is already onboarded cannot be onboarded again: refused before either control is asked | `onboard(00445790, tesco)` | refused: `already onboarded` | [`0x9036cd1b…`](https://explorer-studio-dev.genlayer.com/tx/0x9036cd1b69759e8113b9dc740b260368e3d1c0f74c701a996b432544249aeada) 3 agree |

After the run `CounterpartyGate.get_config()` reports 3 counterparties onboarded and 2 payments made; `SanctionsScreen.is_cleared(subject, 86400, 30)` is true for: `tesco`, `sainsbury`, `peninsula`, `apple`, `santander`.

## What the live run found

- **Plain code caught what a lookup would miss, and the validators agreed on every one.** A Monero address and a checksummed Ethereum address (Valerian Labs) matched an SDN entry's remarks with no name given, and a clean name (`Tesco PLC`) carrying a Tron address from Bank Markazi's remarks was still an `ADDRESS_MATCH`.
- **The reader only escalated, and only what plain code could not settle.** `Mahan Airlines` (the entry is `MAHAN AIR`) and `Kadhafi Muammar` (the entry is `QADHAFI, Muammar`) have no shared exact name, so plain code listed the resembling entries and the validators' LLMs each picked the same one (#12927, #12606): `POSSIBLE_MATCH`, never a clearance. `Apple Inc` and `Banco Santander SA` resembled 1 and 2 entries, and every validator dismissed them: `NO_MATCH`.
- **What it cannot decide stays undecided.** `Trading Company Limited` has no distinctive word, so it is `UNDETERMINED` and the gate refuses it; `Sberbank Group` resembles 19 entries, more than a reader may be asked about, so it is a `POSSIBLE_MATCH` without asking anyone.
- **The gate asks both controls, every time.** CounterpartyGate onboarded a company only when KYB Desk approved it **and** SanctionsScreen cleared its paired subject; each of `NAME_MATCH`, `ADDRESS_MATCH`, `POSSIBLE_MATCH` and `UNDETERMINED` was refused with SanctionsScreen's verdict in the message, and a company KYB Desk does not approve was refused with the sanctions subject clean.

## Superseded deployments

| Contract | Address | Why it is superseded |
|---|---|---|
| SanctionsScreen (test instance) | `0xA24D7bEF58E85F98e68F66d5b1d05fB578dC855A` | Deployed while the matching rules were still being tuned against the real list; four probe subjects only. Replaced by a clean deployment of the final code. |

## Proven in tests, not live

Direct Mode proves these on the real list (or the real list with one marked field changed); none has a live transaction:

- Every way a list can fail to parse (truncated, a stray column, a duplicate or non-numeric id, an alias of an unknown entry, a bare carriage return), a list published at two times, a missing or unreadable `Last-Modified`, a list older than 30 days, exactly 30 days old, or dated in the future.
- The reader refusing to be asked for what plain code decided, and a reader whose answer is not JSON, names an entry it was not shown, or raises.
- The validators' consensus boundary: tampered facts, a leader that hides or flips the reading, a reading of nothing, malformed readings.
- Every CounterpartyGate check that runs before its cross-contract calls (owner, amount, constructor limits, paying a company never onboarded). Its checks that read KYB Desk and SanctionsScreen, and the refusal to onboard a company twice, are proven by the live table above, because Direct Mode cannot simulate a cross-contract call or a first successful onboard. A *stale* approval or screening has no live refusal (it would need a day to pass).
- The replay: `test_the_fixtures_reproduce_what_the_validators_agreed_on_live` runs every live screening again on the committed OFAC files and requires the same facts (down to the file hashes), verdict, reasons and matches.
