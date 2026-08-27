# Job Research Match Skill development plan

This English document is the primary version. The `.ko.md` file is an ancillary
Korean translation.

## Completed scope

- Removed the former crawler application, dashboard, server, and MCP architecture
- Established a `SKILL.md`-centered structure shared by Codex and Claude Code
- Defined input precedence for tagged documents and prompt-written profiles
- Added posting normalization and explainable matching policies
- Added login and private local-state safeguards
- Added explainable, deletable preference memory
- Added on-demand and cron/agent automation guidance
- Added the privacy preflight scanner and release allow-list
- Added public platform field/transport catalogs without candidate-specific values

## Next evaluation stages

1. Validate behavior with synthetic profiles and postings that contain no personal
   data.
2. Check profile extraction accuracy using a document explicitly tagged by the
   user.
3. Review scores and levels against a sample of active postings.
4. Verify each platform's login-session behavior interactively where authorized.
5. Create and test a schedule only after an on-demand run succeeds.

Stages involving a real resume, career document, or login session require the user
to name or authorize that input in the current request.
