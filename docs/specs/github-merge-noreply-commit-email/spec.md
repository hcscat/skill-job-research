# GitHub web-merge noreply commit email

## Purpose

`scripts/privacy_check.py --git-history` verifies that reachable commits use approved non-personal author and committer metadata. GitHub web pull-request merge commits set the committer to `GitHub` with local-part `noreply` at `github.com`. The history scanner must accept that exact commit metadata address while keeping all other `@github.com` addresses blocked in commit metadata and leaving file-content email scanning unchanged.

## Rules

- `ALLOWED_EMAIL_DOMAINS` remains `{"example.com", "users.noreply.github.com"}`; do not add `github.com` as an allowed domain.
- `ALLOWED_COMMIT_EMAILS` in `scripts/privacy_check.py` contains only the single normalized address for GitHub web-merge commits (`noreply` at `github.com`), compared case-insensitively after stripping surrounding whitespace.
- `scan_git_history` accepts a commit author or committer email if and only if its normalized address is in `ALLOWED_COMMIT_EMAILS` or its domain is in `ALLOWED_EMAIL_DOMAINS`.
- Commit name checks remain unchanged: `ALLOWED_COMMIT_NAMES` already includes `"github"`, and non-generic commit names paired with `noreply` at `github.com` remain rejected as `non-generic commit name metadata`.
- `scan_blob` (used by working-tree, `--all-files`, `--staged`, and history tree scans) is unchanged: it only exempts `ALLOWED_EMAIL_DOMAINS` and continues to report `noreply` at `github.com` and any other `@github.com` address appearing in file content.

## Test cases

| ID | Scenario | Setup and input | Expected result | Check |
|---|---|---|---|---|
| TC-01 | GitHub web-merge committer metadata | Temporary Git repo with author `example-handle` (`12345+example-handle@users.noreply.github.com`) and committer `GitHub` (`noreply` at `github.com`); run `scan_git_history` | Returns `[]` (no findings) | `tests/test_privacy_history.py::PrivacyHistoryTest::test_github_web_merge_noreply_committer_passes` |
| TC-02 | Case-insensitive exact match | Temporary Git repo with committer `GitHub` and mixed-case `NoReply` at `GitHub.com`; run `scan_git_history` | Returns `[]` (no findings) | `tests/test_privacy_history.py::PrivacyHistoryTest::test_github_web_merge_noreply_committer_is_case_insensitive` |
| TC-03 | Other `@github.com` commit email blocked | Temporary Git repo with committer `GitHub` (`someone` at `github.com`) and another commit with author `Release Bot` (`someone` at `github.com`); run `scan_git_history` | Reports `non-noreply commit email metadata` for each commit without exposing the email value | `tests/test_privacy_history.py::PrivacyHistoryTest::test_other_github_domain_commit_email_is_rejected` |
| TC-04 | Non-generic commit name with GitHub noreply email | Temporary Git repo with committer `Real Person` and `noreply` at `github.com`; run `scan_git_history` | Reports `non-generic commit name metadata` (and no email finding) | `tests/test_privacy_history.py::PrivacyHistoryTest::test_non_generic_name_with_github_merge_noreply_is_rejected` |
| TC-05 | File-content scanning unchanged | Run `scan_blob` on synthetic text containing `noreply` at `github.com` and `someone` at `github.com` | Both are reported as `email address` | `tests/test_privacy_history.py::PrivacyHistoryTest::test_file_content_scan_still_rejects_github_noreply_and_domain_emails` |

## Unchanged on failure

`scripts/privacy_check.py` only reports findings and exits non-zero; it never rewrites Git history, commits, or working files.
