# Contributing

Conventions for branches, commits and pull requests in this repo. They are short on purpose —
everything here is enforceable by reading a diff.

## Branches

`main` is protected by convention: never commit to it directly, never force push it.
Every change starts from an up-to-date `main`:

```bash
git switch main && git pull
git switch -c feat/order_cancel_flow
```

Format: `<prefix>/<short_name>` — lowercase, `snake_case`, three or four words at most.

| Prefix | Use for |
| --- | --- |
| `feat/` | New behaviour: an event, a worker, an endpoint |
| `fix/` | Bug fix in existing behaviour |
| `refactor/` | Restructuring with no behaviour change |
| `docs/` | README, architecture notes, diagrams |
| `test/` | Tests only |
| `chore/` | Tooling, deps, compose, Makefile, CI |
| `perf/` | Performance work with a measured result |

Examples: `feat/dead_letter_topic`, `fix/reservation_release`, `chore/pin_confluent_kafka`.

## Commits

Every commit message starts with the tag matching the branch prefix:

```
[feat] emit order.cancelled from the matching worker
```

| Tag | Meaning |
| --- | --- |
| `[feat]` | New behaviour |
| `[fix]` | Bug fix |
| `[refactor]` | No behaviour change |
| `[docs]` | Documentation |
| `[test]` | Tests |
| `[chore]` | Tooling, dependencies, infra |
| `[perf]` | Performance |

Rules:

| Rule | Why |
| --- | --- |
| Imperative mood, lowercase after the tag, no trailing period | Reads as "apply this commit and it will…" |
| Subject line ≤ 72 characters | Stays readable in `git log --oneline` |
| One logical change per commit | A revert should never undo two unrelated things |
| Body explains **why**, not what the diff already shows | The diff is the what |
| Blank line between subject and body, body wrapped at 72 | Standard git formatting |
| No debug `print`, `console.log` or commented-out code | Caught in review otherwise |
| New dependency gets its own `[chore]` commit and a note in the PR | Makes the dependency decision reviewable on its own |

Body and footer:

```
[fix] release the cash reservation on partial cancel

The risk worker only released the full notional, so a cancel after a
partial fill left funds locked until restart. Release the remaining
quantity instead.

Co-Authored-By: Someone Else <someone@example.com>
```

## Pull requests

| Item | Expected |
| --- | --- |
| Title | Same format as the commit: `[feat] add dead letter handling` |
| Base | `main` |
| Size | Reviewable in one sitting; split otherwise |
| Description | The template in `.github/pull_request_template.md`, filled in |
| Tests | `make test` green, new behaviour covered |
| Merge | Squash merge, keeping the tagged title as the squash subject |
| History | Never `git push --force`; push a new commit instead |

Because this is an event-driven system, a PR that touches the log says so explicitly:
any new topic, new event type, renamed field or changed payload shape belongs in the
**Events & topics** section of the description and in `docs/architecture.md` in the same PR.
Consumers replay history, so a payload change is a compatibility decision, not a detail.
