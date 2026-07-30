# The gate seen red, before the fix

Command: `python -m exam.tools.check_artefact_locations`, run against
`exam/artifacts/build_manifest.json` as it stands at `8a5a83f9` (origin/master
at the time this ticket was claimed), with everything else at the fixed state.
A gate nobody has watched fire is not a gate.

```
artefact locations: 4 finding(s) in 41 tracked files under exam/artifacts
  exam/artifacts/build_manifest.json                   windows absolute path    papers cheater_brief_path C:\Users\user\Desktop\theoria\.worktrees\v6
  exam/artifacts/build_manifest.json                   worktree segment          C:\Users\user\Desktop\theoria\.worktrees\v6-v23-large-space\exam\artifacts\cheate
  exam/artifacts/build_manifest.json                   backslash path separator ers cheater_brief_path C:\Users\user\Desktop\theoria\.worktrees\v6-v23-la
  exam/artifacts/build_manifest.json                   building user's name     s cheater_brief_path C:\Users\user\Desktop\theoria\.worktrees\v6-v23-large

A tracked generated artefact must not record where its builder stood: it churns on every rebuild, it is a merge-conflict generator between two branches that agree, and archive_run.py carries it into the release manifest. Fix the generator, then regenerate -- generated files are never hand-edited.
exit status: 1
```

Four independent patterns fire on the same file and no other file matches any
of them, which is the shape the ticket predicted: one file, twelve values,
the other 40 artefacts clean. Restoring the regenerated artefact returns
`41 tracked files ... none records where it was built`, exit 0.

The paths named are `.worktrees/v6-v23-large-space` -- this session own V6-V23
delivery, merged hours earlier. The churn is not hypothetical and not old.
