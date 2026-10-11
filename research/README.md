# Research: what GenVM can read and compute, before SanctionsScreen was built

Every source was fetched **from inside GenVM on Studio Next**, not from a laptop, because a source can answer a validator differently from a person, and because a screening contract that parses 6.8 MB per verdict only works if the parse fits inside a transaction. A throwaway probe contract did the work ([`probe_studio_next.py`](probe_studio_next.py), deployed at [`0xb9469F3d10cFb7EcF03CEa80c4DA1345D3bb279b`](https://explorer-studio-dev.genlayer.com/address/0xb9469F3d10cFb7EcF03CEa80c4DA1345D3bb279b)): `probe_csv(url, needle)` fetches a file, parses it with `csv`, counts rows by width and searches it.

## The OFAC publication service

| Call | From GenVM | Same file fetched locally |
|---|---|---|
| [`probe_csv`](https://explorer-studio-dev.genlayer.com/tx/0xdf85d4fa7bef3617ee9ea877b89fccca85fb4d7663dda2d0351671a65a3cb8e8): `SDN.CSV`, 5.7 MB | 200; **5,727,333 bytes**; 19,417 rows (19,416 of 12 columns and one row holding only a Ctrl-Z); 106 rows mention a "Digital Currency Address"; `Last-Modified: Fri, 09 Oct 2026 14:01:35 GMT`; all of it in about five seconds | 5,727,333 bytes, the same SHA-256 |
| [`probe_csv`](https://explorer-studio-dev.genlayer.com/tx/0x56bf1aabaeaac867d904ac75cfba88e98f9612f890647b3add55d7c6573d2e7f): `ALT.CSV`, 1.1 MB | 200; **1,063,323 bytes**; 20,183 rows (20,182 of 5 columns and the Ctrl-Z row); the **same** `Last-Modified` | 1,063,323 bytes |

What this decided:

- **OFAC's own service, both files, whole.** `sanctionslistservice.ofac.treas.gov` (the place `treasury.gov/ofac/downloads/sdn.csv` redirects to) serves validators the same bytes as anyone, with a `Last-Modified` header that is the list's own publication time. The contract records that time and the SHA-256 of both files with every verdict, so a result names exactly which list it was made against.
- **The two files are published together**, so different `Last-Modified` values mean one of them is not the one parsed here (fail closed).
- **A full parse is affordable.** A transaction that downloads, parses, indexes and matches 39,598 names finished in about 20 seconds with three validators agreeing (CONTRACT.md).
- **`unicodedata` is available** ([probe](https://explorer-studio-dev.genlayer.com/address/0x20da60d51C475Bc45f53CeE69802B56a1eA415eb)): accents fold properly (`Muḥammad Gaddāfī` → `Muhammad Gaddafi`); a few letters such as `Ł` need a small map. `difflib`, `math` and `collections` exist too; the contract needs none of them, and does its matching with integers only so that every validator computes the same answer.

Two other official lists were measured locally and **not used**: the UK OFSI consolidated list (16.6 MB) and the EU consolidated financial sanctions file (16.5 MB, 25 seconds to download). A screening that also had to parse those in every validator is a different design; this one screens against OFAC and says so.

## What a real-data prototype taught the matching design

The matching was prototyped in plain Python on the real files before it was written as a contract, and four things changed:

- **Words that are common among sanctioned names are not "generic".** The first scoring weighted a word by how rare it is *among SDN names*, so `Hizballah` and `Mahan` (frequent because they are sanctioned) counted as generic and were never matched. What is generic is a business word (`trading`, `bank`, `group`) or a legal form, in any language OFAC transliterates: `liability`, `joint`, `stock`, `obshchestvo`, `ogranichennoi`. A word's weight now comes from how many names contain it or a spelling variant of it, and a name with no word below 400 occurrences is "too generic to screen".
- **A fuzzy match must never be a strong match.** `Tesco` was one letter from the alias `TEACO`, and `Binance Holdings` matched `Holding Finance` word for word (`binance`↔`finance`, `holdings`↔`holding`). Spelling variants therefore only *nominate* entries for the reader, and only for long words; plain code's strong tier needs exact shared words.
- **A missing word is the common case.** `Mahan Airlines` for `MAHAN AIR`, `Bank Markazi Jomhouri Islami` for `... ISLAMI IRAN`. Entries are scored on how much of the subject they cover and how much of the entry the subject covers, so extra and missing words are both handled.
- **Some names resemble too many entries to review.** `Sberbank Group` shares its one distinctive word with 19 sanctioned entities. A reader shown eight cannot be said to have cleared it, so it is a `POSSIBLE_MATCH`, not a coin flip over which eight are shown.
