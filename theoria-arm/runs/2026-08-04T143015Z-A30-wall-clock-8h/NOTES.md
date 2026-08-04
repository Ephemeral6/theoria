# 2026-08-04T143015Z-A30-wall-clock-8h · running notes

Prompt A30 · branch agent/a30-wall-clock-8h · base 18e7d81
Opened 2026-08-04T14:30:15Z

## 2026-08-04T14:30:16Z

A30 raises the unattended wall clock 3h -> 8h, per owner instruction. WHY IT MATTERS: A26 asks 'given enough money, can the arm win once', and g50t level 1 wants 78 actions. At the measured 11.2-20.7 actions/hour a 3h ceiling tops out at 34-62, so money went up 4.8x while the clock did not move and the experiment could not reach its own question -- it would have recorded 'time ran out' as 'money could not win either'. A26b was in flight when this landed; a running leg parsed its args at start, so this changes the NEXT launch, not that one.

## 2026-08-04T14:30:16Z

IT WAS NOT A ONE-LINE CHANGE, for two reasons found by looking rather than assumed. (1) FOUR COPIES of 3*3600 existed: inner/loop.py:69 DEFAULT_WALL_CLOCK_S, harness/run.py:567 argparse default, armtools/spend_check.py:251 argparse default, harness/spend.py:684 plan_caps default. Changing one leaves three. The constant now lives in harness/spend.py and the other three import it; dependency direction allows this (inner already imports harness, not the reverse), and grep confirmed DEFAULT_WALL_CLOCK_S had no external consumers before the move. (2) A LATENT DEFECT the change would otherwise have triggered: TTL_MAX_S was 8*3600 exactly, and the lease formula was max(TTL_MIN_S, min(TTL_MAX_S, wall_clock + TTL_MARGIN_S)). At wall_clock == 8h the clamp eats the entire 900s margin and returns a lease expiring at the same instant the run is told to stop -- while inner/loop.py:427 stops on `elapsed > wall_clock_s`, i.e. AFTER exceeding, so the last desk call can still be in flight against an expired lease. The comment three lines above TTL_MARGIN_S already forbids this: 'An expired lease cannot be renewed, so the lease is sized to outlive the run rather than to be rescued mid-flight.' The comment and the constant contradicted each other only once the wall clock reached TTL_MAX_S, which is why 3h never exposed it.

- Repair note: the line above lost `elapsed > wall_clock_s` when it was written --
  backticks inside a double-quoted bash argument are command substitution, and
  bash reported `elapsed: command not found` while writing the note itself.
  Restored via a heredoc. Every backticked identifier in a note passed as a
  shell argument disappears the same way, silently apart from that one stderr
  line; check notes after writing them.

## 2026-08-04T14:41:50Z

THE BACKTICK ACCIDENT HAD A SECOND HALF I DID NOT SEE UNTIL A GUARD CAUGHT IT. Writing an archive note through a double-quoted bash argument, the backticks around an identifier opened command substitution -- and inside it the > was a REDIRECT, so bash both ate the text and created an empty file named wall_clock_s at the worktree root, outside the declared territory. I noticed the eaten text (there was a stderr line) and repaired it, and I did not notice the file. The boundary guard did: "1 stray: wall_clock_s", 0/1 green. Removed (0 bytes, untracked); boundary now 1/1, sealed 2/2, secret 5/5. LESSON, sharper than the one already in my notes: the failure mode is not only "backticked identifiers vanish" but "the shell executes what is inside them", and a redirect leaves an artefact somewhere nobody looks. Use a heredoc for any prose containing backticks, and read the boundary guard as a real check rather than a formality -- it is the only thing that saw this.
