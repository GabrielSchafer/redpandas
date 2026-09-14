## Summary

<!-- What changes and why, in two or three lines. -->

## Motivation

<!-- The problem, the bug, or the behaviour that was missing. Link the issue if there is one. -->

## Events & topics

<!-- Fill in or write "none". New topics, new event types, renamed fields, changed payloads.
     A changed payload affects consumers replaying history — say how old events stay readable. -->

| Change | Topic / event | Compatible with existing history? |
| --- | --- | --- |
|  |  |  |

## How to test

```bash
make up && make topics
make worker-ledger / worker-risk / worker-matching / api
make seed
make test
```

<!-- Add the specific steps or requests that show the change working. -->

## Checklist

- [ ] Branch follows `<prefix>/<short_name>`
- [ ] Commits start with the tag (`[feat]`, `[fix]`, …)
- [ ] `make test` passes
- [ ] No debug prints or commented-out code
- [ ] New dependencies are called out above
- [ ] `docs/architecture.md` updated if topics or events changed
