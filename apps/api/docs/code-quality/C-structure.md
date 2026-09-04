# Track C: Structure

Back to [README](./README.md).

Nothing in this track is a defect. Each item is a place where the code works but
the structure will cost something later.

---

## BE-C01: Three notification handlers are `TODO` with a debug log

**Severity:** 🟡 Medium · **Effort:** M · **Status:** ⬜ Todo

**Problem.** `app/shared/events/handlers.py` has three handlers whose body is a
`logger.debug("Would notify ...")` and a commented-out call, at lines 93, 111
and 132. One of them fires on user suspension.

These are the only three `TODO` markers in the whole of `app/` and `scripts/`,
which is a good sign for the codebase generally. The problem is not the marker,
it is that the handler is wired to a real domain event and silently does nothing
at `debug` level, so in production the event fires, the handler runs, and no
notification is sent and no warning appears.

**Recommended fix.** Decide whether these are in scope. If they are, implement
them. If they are not, either unregister the handlers so nothing appears to
handle the event, or raise the log level to `warning` so an unimplemented
notification path is visible in production logs rather than invisible.

**Acceptance criteria**

- [ ] Each handler either sends a notification or is not registered.
- [ ] No handler is wired to an event and silently does nothing at `debug`.

---

## BE-C02: `password_hash` is read through `getattr(user, "_password_hash")`

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo

**Problem.** `UserEntity._password_hash` is declared private at
`app/domain/entities/user.py:41`. Two route modules reach past that:

- `app/api/routes/auth.py:208`
- `app/api/routes/users.py:380`

Both use `getattr(user, "_password_hash", None)` with a default, so if the
attribute is ever renamed both calls silently return `None` rather than raising.
The mapper and the use case access the field directly, so the string form
appears in two of four call sites and a rename would fix half of them.

The symptom is what makes this expensive: in `auth.py` the `None` path raises
401 with "Password not set for this user", so a rename presents as every
password login failing with a plausible business message. Someone chasing that
would read the password flow, the hashing and the user records, and none of
those would be wrong. It is the class of failure that surfaces as a believable
error rather than a crash.

**Recommended fix.** Put the credential check on the entity, where the field
lives: a `verify_password(plaintext)` method, or a `has_password` property plus
an explicit accessor. The routes then ask the entity a question instead of
reaching into it, the import-linter's domain purity contract still holds because
`verify_password` already lives in `app/core/security.py`, and a rename becomes
a type error rather than a silent `None`.

**Acceptance criteria**

- [ ] No `getattr` with a string literal for a private attribute in route code.
- [ ] Renaming the field produces a type error, not a 401.
- [ ] `pnpm typecheck:api` still passes.

---

## BE-C03: Docstrings are the source of the published API contract

**Severity:** 🟢 Low · **Effort:** XS · **Status:** ⬜ Todo

**Problem.** Route and enum docstrings become `description` and `summary` in
`schema/openapi.json`, which is committed, and that file generates
`apps/web/src/api/generated/schema.ts`, also committed. So an edit to a Python
docstring invalidates two checked-in artifacts and fails `pnpm contracts:check`
until they are regenerated.

This was demonstrated by the em-dash sweep in this same session: editing
docstrings for prose reasons changed 24 lines of `openapi.json`, all of them
description or summary text, with no structural change. Both artifacts were
regenerated and committed with the sweep.

Nothing here is broken. `contracts:check` exists precisely to catch it, and it
did. The cost is that it is not obvious from inside a Python file that a comment
edit has a downstream artifact, so the failure arrives at CI rather than at the
edit.

**Recommended fix.** A pre-commit hook that runs `contracts:sync` when a file
under `app/api/routes/` or `app/domain/enums/` changes, or a line in
`apps/api/README.md` next to the docstring conventions saying that docstrings are
published. The hook is better; the note is a minute's work.

**Acceptance criteria**

- [ ] A docstring edit either regenerates the contract automatically or produces
      a local warning before CI.

---

## BE-C04: A second unused virtualenv sits at the repo root

**Severity:** 🟢 Low · **Effort:** XS · **Status:** ⬜ Todo

**Problem.** There are two virtualenvs: `apps/api/.venv`, which is the project
environment `uv` uses, and `/.venv` at the repo root, 141 MB, created by `uv`
0.12.3 with prompt `eap`.

Nothing references the root one. It is not in `package.json`, CI, or
`.pre-commit-config.yaml`. Its only observable effect is that every `uv run`
command prints:

```
warning: `VIRTUAL_ENV=/Users/piira/Developer/sandbox/eap/eap/.venv` does not
match the project environment path `.venv` and will be ignored
```

on every single invocation, because a shell has it activated. Both are correctly
gitignored, so this is local-machine hygiene rather than a repo problem. Worth a
ticket only because the warning appears on every command and trains people to
ignore `uv`'s output.

**Recommended fix.** Deactivate and delete the root virtualenv, and use
`apps/api/.venv` via `uv run`. If a root environment is wanted for tooling,
point `VIRTUAL_ENV` at the project one instead so the warning stops.

**Acceptance criteria**

- [ ] `uv run` produces no `VIRTUAL_ENV` mismatch warning.
- [ ] One virtualenv for the API, in one place.

---

## Considered and not raised

Recording these so the next reviewer does not spend time on them.

- **`except Exception` appears 16 times in `app/`.** Checked: none is a bare
  `except:`, none is `except Exception: pass`, and `ruff`'s `S110` rule is
  enabled to catch the latter. Each one reviewed had a logged reason. Not a
  finding.
- **No `selectinload` or `joinedload` anywhere in the repositories.** This looks
  like an N+1 risk, but the mappers read only columns off the model, and the
  aggregates that have children store them as JSONB on the parent row
  (`engagement_model.py:3` explains the choice). No eager loading is needed
  because nothing lazy-loads. Revisit if a mapper starts traversing a
  relationship.
- **`print()` in application code.** None. All output goes through the
  structured logger.
- **Tracked build artifacts.** None. `.gitignore` covers all four tooling caches
  and both virtualenvs, and no cache file is tracked.
- **`utc_now` vs `datetime.now()`.** One helper, 251 call sites, no competing
  direct calls in `app/`.
