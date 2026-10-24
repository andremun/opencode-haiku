---
name: pr-review
description: Review a branch, a pull request or the working tree of this repository against REVIEW.md, with the ste-writing and scientific-computing skills. Use for "review this PR", "review the branch" or before a merge.
allowed-tools: Read, Grep, Glob, Skill, Bash(make check), Bash(make lint), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(git show:*), Bash(grep:*), Bash(sed -n:*), Bash(head:*), Bash(wc:*), Bash(ls:*)
---
You review a change. You do not edit files.

1. Find the change. Default: `git diff main...HEAD`. With a PR number, use the PR
   diff. Sort the changed files into code, prose (`*.md`, comments, commit messages)
   and record or generated files.
2. Read `REVIEW.md` and `AGENTS.md`. They set the severity and the paths to skip.
3. Run `make check`. Compare its failures with `main`. Report only new failures.
4. Code: load the `scientific-computing` skill (Skill tool,
   `anthropic-skills:scientific-computing`). Check each changed code file against its
   sections 2 (headers, but MIT here), 3 (ASCII), 4 (central configuration),
   7 (module docstrings), 10 (verification), 12 (numerical correctness) and
   15 (contracts) where they apply.
5. Prose: load the `ste-writing` skill (`anthropic-skills:ste-writing`). Run its
   self-lint on each changed paragraph and on the commit messages
   (`git log main..HEAD`). Report a line only when it breaks a rule. Quote the line and
   give the corrected text.
6. Results: when the change adds or edits a results table or a number in a document,
   load `anthropic-skills:numeric-traceability`. Check that the number traces to a
   named tool and a dated results folder.
7. Plans and decisions: when the change edits a specification or an ADR, check it
   against `anthropic-skills:software-refactor-spec` (decision record, version,
   acceptance checks).
8. If a skill is not installed, use the rules that `REVIEW.md` states. Say in the
   report which skills ran.
9. Report a table: file:line, finding, evidence, severity (Important or Nit). At most
   five Nits. End with one line: MERGE, MERGE AFTER FIXES or REWORK.
