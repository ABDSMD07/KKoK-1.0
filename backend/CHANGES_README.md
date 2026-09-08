# What changed in this copy

I did NOT rewrite your whole backend. Everything not listed below is
untouched — Layout, Composer, Extraction, Normalization, Validation,
Duplicate Detection, Confidence Scoring, and Human Verification are
your original files, byte-for-byte, because they're already tested
and working in isolation. Rewriting working code would only risk
breaking it.

Only 4 files changed:

## 1. `htr/htr_engine.py` — real bug fix
`decoder_start_id` was hardcoded to the IndicBART `<2en>` (English)
tag at load time. Every call, regardless of the document's actual
language, was being told "output English." This would have silently
produced wrong/garbage output the moment you fed it Hindi or
Marathi handwriting.

Fixed: `predict()` now takes a `language` argument (`"hi"`, `"mr"`,
or `"en"`, defaults to `"hi"`). Example:
```python
engine = HTREngine()
text = engine.predict("some_image.png", language="mr")   # Marathi
text = engine.predict("some_image.png", language="hi")   # Hindi (default)
```
**You must verify this yourself**: I can't download the tokenizer
here (no internet access in my sandbox), so I added a load-time check
that prints a WARNING if `<2hi>` or `<2mr>` don't actually exist in
`ai4bharat/IndicBART`'s vocabulary. Watch your console output the
first time you run this — if you see that warning, the language tag
needs a different string (check IndicBART's own docs/vocab for the
exact tag).

## 2. `ocr/ocr.py` — PSM made configurable
`--psm 6` ("assume one uniform block of text") is a poor fit for a
form/table document. Changed the default to `--psm 4` ("assume a
single column of variable-sized text") and made it a parameter
instead of hardcoded, so you can A/B test:
```python
process_document(processed_dir, lang="eng", psm=4)   # new default
process_document(processed_dir, lang="eng", psm=11)  # try if 4 is worse
process_document(processed_dir, lang="eng", psm=6)   # old behavior
```
**You must test this yourself** on your real sample images — I have
no way to run Tesseract against your actual documents here. Compare
word-level confidence scores (already in your OCR output) across
psm=4, 6, and 11 and keep whichever wins.

## 3. `main.py` — full pipeline wired end-to-end
Previously stopped after OCR. Now, after OCR succeeds, it runs:

```
Layout -> Composer -> Extraction -> Normalization -> Validation
   -> Duplicate Detection -> Confidence -> Human Verification
   -> (auto-finalize + Postgres persist)  OR  (Pending Review)
```

New document statuses you'll see: `Pipeline Processing`,
`Pending Review`, `Verified`, `Pipeline Failed`, `Persistence Failed`.

A `human_verification_result.json` is now saved to
`digitalized/<document_id>/` for EVERY document, whether or not it
needed human review — this is the artifact a future review UI would
load to let a reviewer act on pending fields via
`apply_field_decision()` (already in your `verification_engine.py`,
just not called anywhere yet — that's your next real piece of work,
not something I built here since there's no review UI yet).

Also added `fetch_existing_records_for_duplicate_check()` — queries
Postgres `land_record_fields` and reshapes rows back into the
`{"fields": {...}}` format `detect_duplicates()` expects. Returns an
empty list (safely) if Postgres isn't reachable yet or has no rows —
expected on your very first successful run, since duplicate
detection needs at least one prior persisted record to compare
against.

## 4. `database/db_persistence.py`
No logic changes — confirmed `DatabasePersistence().persist(dict)`
can already be called directly with an in-memory dict (it doesn't
require the file-based `main()` script path). `main.py` now calls it
that way.

---

## What I could NOT verify (no internet in my environment)
- Whether `pip install`-ed packages actually import cleanly together
  (fastapi, sqlalchemy, torch, transformers, paddleocr, etc. are not
  installed in my sandbox — I could only check Python syntax with
  `py_compile`, not run the app)
- Whether IndicBART's tokenizer actually contains `<2hi>` / `<2mr>`
  tags (see the WARNING check added in `htr_engine.py` above)
- Whether PSM 4 actually beats PSM 6 on YOUR scanned documents —
  this is an empirical question only your test images can answer
- Whether the Postgres schema/credentials in `db_config.py` are
  correctly set up on your machine

## What to do next
1. Drop your `venv` in as usual, run the app, upload one test image.
2. Watch the console — you should now see it progress through
   `CV -> OCR -> Pipeline Processing -> Verified` or
   `-> Pending Review`, instead of stopping at `OCR Completed`.
3. If it fails at "Pipeline Failed", the traceback will point at
   exactly which stage broke — paste that back to me and I'll help
   debug the specific error, not guess blind.
4. Once you see `Pending Review` documents, that's your next real
   feature to build: a review endpoint/UI that loads
   `human_verification_result.json` and calls `apply_field_decision()`
   per field, then `finalize_verification()`.
