# Private build notes — template

ADR-017 keeps facts specific to CVC's Simpro build and host out of tracked
files. They live in `docs/simpro/private/`, which is git-ignored, mode 0700,
and backed up by `scripts/backup.sh`. Configuration values go in `.env`
instead (see `.env.example`).

On a fresh clone, restore `docs/simpro/private/` from the latest backup
(`private-notes.tar.gz`, or `private-notes.tar.gz.gpg` once a GPG recipient
is set). If no backup exists, create the files below and fill them in.

```bash
install -d -m 700 docs/simpro/private
```

## `docs/simpro/private/cvc-simpro-build.md`

1. **Companies:** the Service and Projects company IDs (also in `.env` as
   `SIMPRO_COMPANY_ID_SERVICE`, `SIMPRO_COMPANY_ID_PROJECTS` and
   `SIMPRO_LIVE_COMPANY_IDS`), the other companies `/companies/` lists, and
   the rule for them.
2. **API application and permissions:** the application's permission level in
   Simpro, the security-group set-up, and what follows for CLIVE's guards.
3. **Environment:** the kind of build CLIVE reads, when access started, and
   which Simpro test environments are or are not used.
4. **Live checks:** dated output of read-only checks that includes IDs or
   record counts.
5. **Host:** where host-specific values are kept (disk IDs, install paths,
   backup target).
6. **Publication tooling:** the files below.

## `docs/simpro/private/public-deny-list.txt`

One pattern per line, `<id><TAB><Python regex>`, `#` for comments. It covers
every value in `cvc-simpro-build.md` that must never appear in a tracked file,
commit message or author field. `scripts/check-public-safe.py` reads it and
exits 2 if it is missing.

## Host copies of tracked templates

- `deploy/smartd/smartd.conf.local`: `deploy/smartd/smartd.conf` with the real
  disk IDs; install it as `/etc/smartd.conf`.
