# Implementation Plan: Gate Repair

## Summary

Repair the gate verdicts and the stage transition so a run cannot report
planning complete while a required finding stays open.

## Delivery Increments

The rescope replaced the earlier slice proposal. Deliver the repair in the
increments below, in order.

| # | Increment |
| --- | --- |
| 1 | Gate verdict model |
| 2 | Gate verdict writer |
| 3 | G3 artifact check |
| 4 | G4 checklist check |
| 5 | G5 task check |
| 6 | G6 findings check |
| 7 | G6.5 confidence read |
| 8 | Stage resolver input |
| 9 | Stage resolver predicate |
| 10 | Finding reconciliation |
| 11 | Transition guard |
| 12 | PR packet input |
| 13 | PR packet emitter |
| 14 | Draft PR body |
| 15 | Ledger reservation |
| 16 | Ledger recovery |
| 17 | Workflow record update |
| 18 | Parity fixtures |
| 19 | Release notes |
