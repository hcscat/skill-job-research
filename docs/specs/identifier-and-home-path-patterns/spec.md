# Identifier and home-path patterns

## Purpose

The publication scanner (`scripts/privacy_check.py`) and the private state validator (`local_state.py`) must reject Korean mobile numbers, resident identifiers and user-home paths wherever they appear in prose, while not flagging hex digests, UUIDs, URL path segments or regex source.

## Rules

- Phone: `01[016789]` or `+82` mobile prefixes followed by 3–4 and 4 digits, with optional `-`, `.` or space separators. Resident identifier: 6 digits, optional `-` or space, then `[1-4]` and 6 digits.
- Both digit patterns use digit-only boundaries. Before they run, recognized UUIDs (`8-4-4-4-12` hex) and hex tokens of 16 or more characters containing a letter are masked. An ordinary word, label or extension next to an identifier does not exempt it.
- Home paths: `/Users/<name>`, `/home/<name>` and `C:\Users\<name>`, bare or nested, at any sentence position, including inside quotes or table pipes. A path segment inside a URL (`https://host/Users/x`) and regex source (an alternation of home prefixes) are not paths.
- In a Git checkout, `--all-files` scans tracked and non-ignored files; an ignore rule never hides a tracked file.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | Contact and resident patterns | Synthetic phone and resident values, alone and next to Korean text, `tel:` or parentheses | Reported | `tests/test_hardening.py::test_public_scanner_rejects_contact_and_resident_patterns`, `test_public_scanner_still_flags_identifiers_next_to_text` |
| TC-02 | Words or extensions next to identifiers | `Call <phone>x123`, `RRN<resident>`, `id ab<phone>` | Reported by the scanner and rejected by the state validator | `tests/test_hardening.py::test_public_scanner_still_flags_identifiers_next_to_text`, `tests/test_local_state.py::test_state_validator_still_rejects_identifiers_next_to_text` |
| TC-03 | Digests and UUIDs | SHA-256, 40-character commit ID and UUID containing phone-shaped digit runs | Not reported | `tests/test_hardening.py::test_public_scanner_ignores_digit_runs_inside_hex_digests`, `tests/test_local_state.py::test_state_validator_ignores_digit_runs_inside_hex_digests` |
| TC-04 | Generic numbers | Build numbers and scores | Not reported | `tests/test_hardening.py::test_public_scanner_keeps_generic_numbers` |
| TC-05 | Home paths in prose | Bare, nested, quoted, pipe-adjacent and Windows home paths | Reported by the scanner; rejected by the state validator | `tests/test_hardening.py::test_public_scanner_rejects_bare_and_nested_home_paths`, `tests/test_local_state.py::test_sensitive_paths_are_rejected_in_any_sentence_position`, `test_home_without_subdirectory_is_still_sensitive` |
| TC-06 | URL segments and regex source | `https://example.com/Users/...`, home-prefix alternations | Not reported | `tests/test_hardening.py::test_public_scanner_ignores_url_segments_and_regex_source`, `tests/test_local_state.py::test_url_paths_are_not_local_user_directories` |
| TC-07 | Checkout scan scope | Temporary repository with an ignored and a non-ignored folder, then the ignored file force-tracked | Non-ignored and tracked files are scanned; the untracked ignored file is not | `tests/test_hardening.py::test_checkout_scan_covers_unignored_files_but_not_an_ignored_local_area` |

## Unchanged on failure

Both checks only report or raise; they never rewrite, redact or delete content. Pattern checks are not proof that every sensitive fact is absent.
