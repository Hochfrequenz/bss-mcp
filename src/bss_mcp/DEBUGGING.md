# BSS Bug Hunt Workflow

Read-only access to the Basic Supply Service (BSS). All tools are safe to call on Prod.

## Identifier reference

| ID | Format example | Used in |
|---|---|---|
| MaLo-ID | `12345678901` (11 digits) | Ermittlungsaufträge, Prozesse |
| Prozess-ID | UUID `xxxxxxxx-xxxx-...` | process state + events |
| Aufgabe-ID | UUID | Ermittlungsauftrag events |

**BSS only knows MaLo — not MeLo.** If you have a MeLo-ID, first find the MaLo via tmds-mcp:
`get_marktlokation` is in TMDS, not BSS.

## Scenario 1: Kundendaten falsch / Ermittlungsauftrag hängt

1. `get_ermittlungsauftraege_for_malo(malo_id)` — all open orders for this MaLo
2. Note the UUID of the suspicious Ermittlungsauftrag
3. `get_events_for_aufgabe(aufgabe_id)` — trace what happened step by step
4. Red flags: missing events, unexpected terminal event, non-continuous sequence (server warns in logs)
5. `get_aufgabe_stats()` — if count is unusually high, this may be a systemic issue

## Scenario 2: Prozess fehlt oder hängt

1. `list_prozesse_for_malo(malo_id)` — all processes for this MaLo
2. Find the suspicious process (check `status` field)
3. `get_prozess_by_id(prozess_id)` — full process state
4. `get_events_for_prozess(prozess_id)` — full event history
5. Red flags: terminal status reached too early, missing expected transition events, timestamp gaps

## Common pitfalls

- Empty list from `get_ermittlungsauftraege_for_malo`: BSS has no record → check if MaLo exists
  in TMDS first via `get_marktlokation`
- `list_prozesse_for_malo` returns 401: OAuth not supported for this endpoint — use BasicAuth config
- Event gaps logged as warnings: deserialization issue in event store — escalate to MAD team
