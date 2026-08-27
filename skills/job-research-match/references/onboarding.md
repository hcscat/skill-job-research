# First-Use Intake And Private Files

Use this workflow during installation, first use, or when the user asks to create or update a saved job-search setup.

## Initialize

1. Run `scripts/local_state.py init` from the installed skill.
2. Keep the generated state outside the Git checkout with owner-only permissions.
3. Do not print the absolute state path in shared output.

Initialization creates non-secret settings, an empty connector-target file, private profile and run directories, and local feedback storage. It never creates credentials, cookies, tokens, or browser exports.

## Gather Only Needed Input

Ask for missing decisions in small groups. Reuse values already supplied in the current request.

- target roles and optional role priorities
- strong skills, support skills, and target industries
- total or discipline-specific career interpretation
- preferred locations and work models
- allowed employment types
- minimum compensation, currency, and undisclosed-compensation policy
- freshness, exclusion, and avoid-keyword rules
- storage and recommendation thresholds
- requested sources and result limit
- optional output spreadsheet, Drive folder, or Gmail label/search scope
- permitted login mode per site: `public-only`, `browser-session`, or `manual`

Do not require a value that the user wants to leave unknown. Do not infer a hard constraint from a preference.

## Create Private Files

1. Summarize the redacted profile and ask whether to persist it when persistence was not already explicit.
2. Create a draft only inside the private local-state `workspace/` directory.
3. Save the validated profile with `local_state.py save-profile --input <private-draft> --name <profile>`.
4. Save connector targets with `local_state.py save-targets --input <private-targets>` only when the user authorized those targets.
5. Configure site login policy with `local_state.py set-login`; never write authentication material.
6. Run `local_state.py privacy-check` after creation or update.
7. Remove an unneeded draft after successful validation when the user authorized cleanup.

The AI may create and update these private files as part of installation or use after authorization. It must not create them under the repository merely because `.gitignore` would hide them.

## Safe Output

Report which private artifact categories were created or updated, their logical names, validation result, and any missing decisions. Do not report absolute local paths, cloud document IDs, account identifiers, or file contents.
