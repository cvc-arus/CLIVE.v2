# CLIVE — Recovery Plan

Where CLIVE's data lives, where its backups go, and how to restore it. Built up
by the course correction sprint's W5 workstream
(`docs/sprints/course-correction/W5-backups.md`); status is in
`docs/STATUS.md`.

## 1. Purpose and scope

The host has two non-RAID SSDs. This plan protects against **one disk
failing**: the backups are kept on the disk that does not hold the data.

It does **not** protect against theft, fire, an accidental `rm`, or
ransomware, because both disks sit in the same always-mounted machine. That
needs an off-machine copy (W5 T7, not yet in place).

## 2. Disk layout

| Disk | Partition | Mount | Size | Holds |
|---|---|---|---|---|
| `sda` | `sda1` | `/boot/efi` | 1G | EFI boot |
| `sda` | `sda2` | `/` | 228G (160G free) | OS, the repository (`~/projects/CLIVE-I`), **backups** |
| `sdb` | `sdb1` | `/data` | 229G (204G free) | **All live CLIVE data**, including Docker's root directory |

Docker's root directory is not the default `/var/lib/docker`; it is
`/data/docker`, on `sdb1`.

Evidence, run on 2026-10-14 against commit `c6b0d96`:

```text
$ docker info --format '{{.DockerRootDir}}'
/data/docker

$ findmnt /data
TARGET SOURCE    FSTYPE OPTIONS
/data  /dev/sdb1 ext4   rw,noatime

$ findmnt /
TARGET SOURCE    FSTYPE OPTIONS
/      /dev/sda2 ext4   rw,relatime

$ lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS /dev/sda /dev/sdb
NAME     SIZE TYPE FSTYPE MOUNTPOINTS
sda    232.9G disk
├─sda1     1G part vfat   /boot/efi
└─sda2 231.8G part ext4   /
sdb    232.9G disk
└─sdb1 232.9G part ext4   /data

$ df -h / /data
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2       228G   56G  160G  26% /
/dev/sdb1       229G   14G  204G   7% /data
```

## 3. Live data per disk

Every mount used by the Compose stack (`docker-compose.yml`, confirmed with
`docker compose config` and `docker inspect` on the running containers):

| Service (container) | Mount type | Host path | Size | Disk |
|---|---|---|---|---|
| `postgres` (`clive-postgres`): Phase 2 pgvector database | bind | `/data/pgvector_data` | 73M | sdb1 |
| `open-webui` (`clive-webui`): SQLite `webui.db` (users, chats, settings), uploads, cache | bind | `/data/openwebui_data` | 22M | sdb1 |
| `simpro-mock-db` (`clive-simpro-mock-db`) | named volume `clive-i_simpro-mock-db-data` | `/data/docker/volumes/clive-i_simpro-mock-db-data/_data` | 64M | sdb1 |
| `ollama` (`clive-ollama`): models | bind | `/data/ollama` | 6.5G | sdb1 |
| `postgres`: init script | bind (config) | `configs/postgres/init-pgvector.sql` in the repository | — | sda2, and in git |
| `tika`, `simpro-mock` | none | — | — | — |

The first three sizes were measured with `du -sh` inside each container,
because the host directories are owned by root or by the container's database
user and cannot be read without root.

## 4. Unmounted directories on `/data`

Six directories on `/data` are not mounted by any current container. They
appear to be left over from an earlier setup.

| Directory | Size | Notes |
|---|---|---|
| `/data/open-webui` | 894M | An earlier Open WebUI data directory: `webui.db` last written 2026-08-05, plus `uploads/`, `cache/` and `vector_db/`. May hold earlier users and chats. The live stack uses `/data/openwebui_data` |
| `/data/postgres` | 46M | Not readable by `clive`; size measured on 2026-10-14 with `du -sh` through a `postgres:16-alpine` container (read-only mount) |
| `/data/qdrant` | 20K | Empty-looking Qdrant store (`aliases/`, `collections/`, `raft_state.json`) |
| `/data/redis` | ≥ 12K | `dump.rdb` and `appendonlydir/` (the latter not readable without root) |
| `/data/backups` | Empty | |
| `/data/documents` | Empty | |

**Decision (2026-10-14, Alex): back up all six.** None of them is deleted.

## 5. Backup target

**`~/clive-backups/`**, on `sda2` (decided 2026-10-14, Alex).

- **Other disk:** all live data is on `sdb1`. If `sdb` fails, the backups on
  `sda` survive. If `sda` fails, the data on `sdb` survives, and the
  repository can be cloned again from GitHub.
- **Outside the repository:** backups do not sit in the git working tree.
- **Owned by `clive`:** a scheduled job running as `clive` can write there
  without root.
- **Space:** 160G free, against about 160 MB of live data (Ollama models
  excluded) and about 940 MB in the unmounted directories.

The directory was created, with mode 700, by the first backup run on
2026-10-14 (§8).

## 6. Notes

Decisions and findings that shape the backup:

- **Root-owned directories.** `/data/pgvector_data`, `/data/openwebui_data`,
  `/data/open-webui`, `/data/postgres` and `/data/redis` cannot be read by
  `clive`. Decision (2026-10-14, Alex): archive them through a throwaway
  container using the `postgres:16-alpine` image, which is already on the host
  and includes `tar`, so no new image is pulled and the timer needs no sudo.
- **`scripts/backup.sh`** used to default to `./backups` inside the
  repository; since W5 T3 it defaults to `~/clive-backups` (§8). `.env` still
  sets the old value (§8, outstanding).
- **Ollama.** Models are not backed up; they are re-pulled. `/data/ollama` also
  holds Ollama's identity key (`id_ed25519`), which Ollama recreates if it is
  missing.

## 7. Backup inventory

Agreed 2026-10-14 (W5 T2). Facts checked on 2026-10-14 against commit
`0087257`. Nothing below is backed up yet; the script is W5 T3.

| # | Item | Size | Method | Notes |
|---|---|---|---|---|
| 1 | Phase 2 Postgres: database `clive` (one table, `document_chunk`) and roles | 18 MB | `pg_dump -Fc` and `pg_dumpall --globals-only`, run inside `clive-postgres` (`pg_dump` 16.14) | Also holds the **knowledge base embeddings**: Open WebUI's `PGVECTOR_DB_URL` points at this database (`docker-compose.yml`). Keep the restore check that `scripts/backup.sh` already does |
| 2 | Open WebUI `webui.db` (users, chats, settings) | about 5.5 MB with its WAL | SQLite online backup through `docker exec clive-webui python3` (its `sqlite3` module is 3.40.1) | No `sqlite3` command exists on the host or in the container. A plain `tar` of a live WAL database can be inconsistent |
| 3 | Open WebUI uploads and cache (`/data/openwebui_data`) | 16 MB and 20K | `tar` through `postgres:16-alpine` | Contains real customer documents |
| 4 | The six unmounted directories (§4) | about 940 MB | `tar` of each through `postgres:16-alpine`, read-only mount | `/data/open-webui` also holds an old Chroma store (`vector_db/chroma.sqlite3`) and no uploads |
| 5 | `.env` | small | **Deferred (2026-10-14, Alex):** key not created yet, so `.env` is not backed up (§8). Planned: encrypted with a GPG **key pair**: the public key on the host, the private key and its passphrase kept off the machine (decision 2026-10-14, Alex) | A scheduled job cannot type a passphrase, so symmetric encryption with an off-machine passphrase is not possible. The host has no GPG key yet |
| 6 | Ollama model list | — | `ollama list` output saved to a text file | Models (`nomic-embed-text`, `qwen2.5-coder:7b`, `llama3.2`) are re-pulled, not backed up |
| 7 | Image versions | — | Each running image's digest saved to a text file | `open-webui:main` and `ollama/ollama` are unpinned tags, so a restore could pull a newer Open WebUI that migrates `webui.db`. Running: Open WebUI 0.11.0. 2026-10-23: pinned to `v0.12.3` and `0.31.2` (ADR-018); a restore uses the tag in `docker-compose.yml`, and the digests recorded here show what ran |
| 8 | Private build notes (`docs/simpro/private/`, ADR-017; added 2026-10-19) | small | `tar` into `private-notes.tar.gz`; encrypted to `BACKUP_GPG_RECIPIENT` as `private-notes.tar.gz.gpg` once that is set | Untracked, so git does not hold them. Until the GPG key exists they are a plain copy protected by the backup folder's 0700 mode (decision 2026-10-19, Alex). Restore: extract into `docs/simpro/private/` with mode 0700 (`docs/simpro/private-notes.template.md`) |

Not backed up:

- **`simpro-mock-db`:** disposable test data, rebuilt from the seed script
  (`docs/installation.md` §9).
- **Source documents:** none outside Open WebUI (`/data/documents` is empty).
- **Git repository:** on GitHub; no bundle.

**Sensitivity:** backups contain customer documents (item 3) and chats
(item 2). The backup directory is to be readable by `clive` only (mode 700),
and the off-machine copy (§11) is to be encrypted.

## 8. Backup procedure and schedule

`scripts/backup.sh` (W5 T3, 2026-10-14). It runs daily at 02:30 from a systemd
timer (W5 T4, below) and can also be run by hand from anywhere.

```bash
./scripts/backup.sh
```

What a run does, in order; any failure stops it with a non-zero exit and a log
line naming the step:

1. Checks the settings, that `clive-postgres`, `clive-webui` and
   `clive-ollama` are running, and that `BACKUP_DIR` is **not** on the same
   disk as `/data`. Creates `BACKUP_DIR` with mode 700; every file is written
   with `umask 077`.
2. Writes into `<BACKUP_DIR>/<YYYY-MM-DD_HHMM>.partial/`:

   | File | Content (inventory item, §7) |
   |---|---|
   | `pgvector.dump`, `postgres-globals.sql` | Phase 2 database (custom format) and roles (1). Restored into a temporary database `clive_backup_test`, which must have the `vector` extension, the same tables, and the same row count in every table as the live database; then dropped |
   | `webui.db` | Online SQLite backup (2), converted out of WAL mode; `PRAGMA integrity_check` must return `ok` |
   | `openwebui_data.tar.gz` | `/data/openwebui_data` without the live `webui.db` files (3) |
   | `data-<dir>.tar.gz` | Each of the six unmounted directories (4) |
   | `env.gpg` | `.env` encrypted to `BACKUP_GPG_RECIPIENT` (5). **Not produced yet**: no key exists, so the run logs a warning and records it in `NOTES.txt` |
   | `ollama-models.txt`, `images.txt` | Model list (6) and each running container's image and digest (7) |
   | `SIZES.txt`, `MANIFEST.txt` | File sizes, and SHA-256 checksums of every file; `sha256sum --strict -c MANIFEST.txt` must pass |

3. Renames the folder to `<YYYY-MM-DD_HHMM>/`. A `.partial` folder is never
   counted as a backup and is never deleted automatically; the run lists any it
   finds.
4. Retention: keeps the newest backup from each of the last
   `BACKUP_RETENTION_DAILY` (7) days that have one, plus the newest from each of
   the last `BACKUP_RETENTION_WEEKLY` (4) Sundays, and deletes other completed
   backup folders.

Settings: `BACKUP_DIR`, `BACKUP_RETENTION_DAILY`, `BACKUP_RETENTION_WEEKLY` and
`BACKUP_GPG_RECIPIENT`, from the environment or from `BACKUP_*` lines in `.env`
(names in `.env.example`). No other `.env` value is read; database credentials
come from the containers' own environment. Whitespace around keys and values
(including a trailing CR) is stripped, and the first occurrence of a key wins.

**Outstanding (Alex):**

- Create the GPG key pair and set `BACKUP_GPG_RECIPIENT` (deferred, 2026-10-14):

  ```bash
  gpg --quick-generate-key "CLIVE backup <you@example.com>" rsa4096 encr never
  gpg --list-keys --with-colons "CLIVE backup" | awk -F: '/^fpr/{print $10; exit}'
  gpg --export-secret-keys --armor <FPR> > <off-machine media>/clive-backup-private.asc
  gpg --delete-secret-keys <FPR>
  ```

### Schedule

W5 T4 (2026-10-14). `deploy/systemd/clive-backup.timer` starts
`deploy/systemd/clive-backup.service` daily at 02:30; both are installed to
`/etc/systemd/system/` (steps in `docs/installation.md` §9).

- The service runs `scripts/backup.sh` from the repository working tree as
  `clive` (a member of the `docker` group), at low CPU and I/O priority. The
  script on the checked-out branch is the one that runs.
- 02:30 avoids the host's other nightly jobs and both UK clock changes
  (01:00–02:00). `Persistent=true` runs a missed backup at the next boot; if
  the containers are not up yet, that run fails and the next night's runs as
  normal.
- A failed backup leaves the unit failed. Failures are only in the journal:
  there is no alerting yet (monitoring, roadmap Phase 10).

```bash
systemctl list-timers clive-backup.timer
systemctl status clive-backup.service
journalctl -u clive-backup -n 30 --no-pager
```

Run on 2026-10-14 against commit `3441d0b` plus the uncommitted unit files,
after Alex installed them:

```text
$ systemctl list-timers clive-backup.timer --no-pager
NEXT                        LEFT LAST PASSED UNIT               ACTIVATES
Thu 2026-10-15 02:30:00 BST  13h -         - clive-backup.timer clive-backup.service

$ journalctl -u clive-backup -n 25 --no-pager
... backup.sh[1690448]: [2026-10-14 12:52:54] === CLIVE backup 2026-10-14_1252 ===
... backup.sh[1690448]: [2026-10-14 12:52:54] Writing to ~/clive-backups/2026-10-14_1252.partial
... backup.sh[1690448]: [2026-10-14 12:52:55]       public.document_chunk: 365 rows (matches live)
...
... backup.sh[1690448]: [2026-10-14 12:53:52] Backup complete: ~/clive-backups/2026-10-14_1252 (830M)
... backup.sh[1690448]: [2026-10-14 12:53:52] Retention: kept 1, deleted 1 (7 daily, 4 weekly)
... systemd[1]: Finished clive-backup.service - CLIVE cross-disk backup (scripts/backup.sh).

$ sha256sum --strict --quiet -c MANIFEST.txt && echo "all OK"
all OK
```

That run was started by hand (`sudo systemctl start clive-backup.service`).
The first run started by the timer is due on 2026-10-15 at 02:30 and is not
yet recorded.

### First run

2026-10-14, commit `a274fe1` plus the uncommitted script, with
`BACKUP_DIR=<home>/clive-backups` (on `/dev/sda2`). Took 59 seconds:

```text
[2026-10-14 11:41:35] === CLIVE backup 2026-10-14_1141 ===
...
[2026-10-14 11:41:37]       public.document_chunk: 365 rows (matches live)
[2026-10-14 11:41:37]       integrity_check: ok
...
[2026-10-14 11:42:30]       WARNING: .env NOT backed up: BACKUP_GPG_RECIPIENT is not set (GPG key pair to be created later; docs/recovery-plan.md section 7)
...
[2026-10-14 11:42:34] Backup complete: ~/clive-backups/2026-10-14_1141 (830M)
[2026-10-14 11:42:34] Retention: kept 1, deleted 0 (7 daily, 4 weekly)
```

```text
$ cat SIZES.txt
89  data-backups.tar.gz
89  data-documents.tar.gz
843703368  data-open-webui.tar.gz
6760312  data-postgres.tar.gz
409  data-qdrant.tar.gz
421  data-redis.tar.gz
767  images.txt
49  NOTES.txt
277  ollama-models.txt
16019637  openwebui_data.tar.gz
1601492  pgvector.dump
665  postgres-globals.sql
1474560  webui.db

$ sha256sum --strict --quiet -c MANIFEST.txt && echo "all OK"
all OK
```

That folder no longer exists: retention keeps the newest backup of each day,
so the run below replaced it.

### Run with the `.env` settings

2026-10-14, commit `c929c1c` plus the uncommitted whitespace fix, run as plain
`./scripts/backup.sh` after Alex updated `.env`:

```text
[2026-10-14 12:35:22] === CLIVE backup 2026-10-14_1235 ===
[2026-10-14 12:35:22] Writing to ~/clive-backups/2026-10-14_1235.partial
...
[2026-10-14 12:35:23]       public.document_chunk: 365 rows (matches live)
...
[2026-10-14 12:36:20] Backup complete: ~/clive-backups/2026-10-14_1235 (830M)
[2026-10-14 12:36:20] Retention: kept 1, deleted 1 (7 daily, 4 weekly)
```

Retention was tested separately against 80 empty dummy folders (two a day for
40 days) in a scratch directory: it kept 10 (the last 7 days plus the Sundays
2026-09-20, 09-27 and 10-04; 10-11 is both) and left a `.partial` folder alone.

## 9. Disk health baseline

W5 T5 (2026-10-14). `smartmontools` 7.4 is installed on the host (a justified
exception to Docker-first: it needs direct hardware access), and `smartd`
monitors both disks with `deploy/smartd/smartd.conf`, installed as
`/etc/smartd.conf` (Ubuntu's original kept as `/etc/smartd.conf.orig`; steps in
`docs/installation.md` §9).

- Checks: health, attributes, error and self-test logs; a short self-test
  daily at 03:00 and a long self-test on Saturdays at 04:00; temperature logged
  at 55 °C, critical at 65 °C.
- Alerts go to the journal only. There is no mail setup on the host, and email
  would need an external SMTP relay; alerting is deferred to monitoring
  (roadmap Phase 10). Nobody is warned unless someone looks, so check:

```bash
systemctl status smartmontools --no-pager      # smartd; "Monitoring 2 ATA/SATA" devices
journalctl -u smartmontools --since "-7 days" --no-pager
sudo smartctl -A /dev/sda | grep -E "^(  5|173|197|198|202) "
sudo smartctl -A /dev/sdb | grep -E "^(  5|173|197|198|202) "
sudo smartctl -l selftest /dev/sda; sudo smartctl -l selftest /dev/sdb
```

### Baseline

Run on 2026-10-14 against commit `45021e8`: Alex ran
`smartctl -x` on both disks after a short self-test, into a file outside the
repository; values copied from that output.

| | `sda` (serial `…902A`: `/`, repository, backups) | `sdb` (serial `…902C`: `/data`, live data) |
|---|---|---|
| Model, firmware | Crucial MX500 250 GB (`CT250MX500SSD1`), M3CR023 | Same |
| `smartctl -H` | PASSED | PASSED |
| Short self-test | Completed without error (the first in the log) | Completed without error (the first in the log) |
| Error log | No Errors Logged | No Errors Logged |
| Power-on hours (9) | 10,898 | 4,457 |
| **Percentage Used Endurance Indicator** (device statistics; also 202 raw) | **129** | **116** |
| Average block-erase count (173) | 1,938 | 1,744 |
| Total LBAs written (246) | 23,582,729,578 (about 12.1 TB) | 20,006,031,404 (about 10.2 TB) |
| Reallocated NAND blocks (5) / pending (197) / uncorrectable (198) | 0 / 0 / 0 | 0 / 0 / 0 |
| CRC errors (199) | 0 | 0 |
| Unexpected power losses (174) | 13 | 12 |
| Temperature (194), min/max | 31 °C (0/56) | 31 °C (0/51) |

```text
===== /dev/sda
SMART overall-health self-assessment test result: PASSED
202 Percent_Lifetime_Remain ----CK   227   227   001    -    129
0x07  0x008  1             129  ---  Percentage Used Endurance Indicator
 # 1  Short offline       Completed without error       00%     10898         -
===== /dev/sdb
SMART overall-health self-assessment test result: PASSED
202 Percent_Lifetime_Remain ----CK   240   240   001    -    116
0x07  0x008  1             116  ---  Percentage Used Endurance Indicator
 # 1  Short offline       Completed without error       00%      4457         -
```

### Finding: both disks are past their rated endurance

- Both disks have used more than their rated write endurance: 129 % (`sda`)
  and 116 % (`sdb`), from the drives' own endurance indicator, consistent with
  the average erase counts against roughly 1,500 rated cycles.
- `smartctl -H` still reports PASSED because attribute 202's normalised value
  wraps below zero (100 − 129 is shown as 227) and stays above its threshold.
  PASSED is therefore not evidence of remaining life on these disks.
- Host writes are modest (about 12 TB and 10 TB), but the drive-internal
  writes are about 32 times higher (attributes 247 and 248), which wears the
  flash much faster than the host workload alone would.
- No reallocated, pending or uncorrectable blocks yet: the disks work today,
  but there is no rated margin left.
- The serial numbers are consecutive (same batch, bought together) and the
  wear is similar, so both could fail close together. The cross-disk backup
  does not cover that case.

Alex's decisions (2026-10-14), all agreed and kept in view, not yet acted on:

1. Off-machine copy (§11, W5 T7): agreed; to be done later.
2. Replace both disks, `sdb` (live data) first.
3. Back up the leftover `/data/open-webui` (about 844 MB, most of each backup)
   once, keep that copy, then exclude it from the daily run to cut writes to
   `sda`. `scripts/backup.sh` is unchanged for now.
4. Look into a firmware update for the M3CR023 firmware (vendor tool and a
   reboot; host change).

## 10. Restore procedure and drill report

W5 T6 (2026-10-14). Two procedures: a **drill** that restores a backup next
to the live stack (drilled, below), and a **full rebuild** after losing `sdb`
(written from the drill, not drilled as a whole).

### Restore drill (side by side with the live stack)

`deploy/restore-drill/compose.yml` defines a separate Compose project,
`clive-drill`, with its own volumes (`clive-drill_pgvector`,
`clive-drill_webui-data`) and ports (Open WebUI `127.0.0.1:3100`, Postgres
`127.0.0.1:5442`). It never touches the live containers, volumes or `/data`.
`drill-webui` joins the live network to use the live Ollama and Tika: models
are not in the backup, and a second Ollama would compete for GPU memory. The
drill therefore tests the restore of **data**, not of models.

Run from the repository root. `B` is the backup folder; the Open WebUI image is
pinned to the one in the backup's `images.txt` and never pulled.

```bash
B=~/clive-backups/<YYYY-MM-DD_HHMM>
export DRILL_WEBUI_IMAGE=$(awk '$1=="clive-webui"{print $3}' "$B/images.txt")
DC="docker compose -p clive-drill --env-file .env -f deploy/restore-drill/compose.yml"

# 1. Checksums
(cd "$B" && sha256sum --strict --quiet -c MANIFEST.txt && echo "all OK")

# 2. Volumes and an empty Postgres
$DC create
$DC up -d --wait drill-postgres

# 3. Phase 2 database. postgres-globals.sql is not needed: it creates only the
#    clive role, which the container creates from POSTGRES_USER.
docker exec -i clive-drill-postgres sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error' < "$B/pgvector.dump"

# 4. Open WebUI files, then the backed-up webui.db over them
docker run --rm --pull=never --network none \
  -v clive-drill_webui-data:/dst -v "$B":/b:ro postgres:16-alpine \
  sh -c 'tar xzf /b/openwebui_data.tar.gz -C /dst && cp /b/webui.db /dst/webui.db'

# 5. Open WebUI
$DC up -d --wait --wait-timeout 300 drill-webui
```

6. Compare row counts. Phase 2 database, every table (run against
   `clive-postgres` and `clive-drill-postgres`):

   ```bash
   docker exec -i clive-drill-postgres sh -c \
     'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F "|" -v ON_ERROR_STOP=1' <<'EOF'
   SELECT format('SELECT %L, count(*) FROM %I.%I;', schemaname||'.'||tablename, schemaname, tablename)
   FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1
   \gexec
   EOF
   ```

   `webui.db`, every table, in the backup file and in the drill's copy:

   ```bash
   cat > /tmp/webui-counts.py <<'EOF'
   import sqlite3, sys
   db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
   for (t,) in db.execute("select name from sqlite_master where type='table' "
                          "and name not like 'sqlite_%' order by name"):
       print(t, db.execute('select count(*) from "%s"' % t).fetchone()[0])
   EOF
   docker run --rm --pull=never --network none --entrypoint python \
     -v "$B":/b:ro -v /tmp/webui-counts.py:/c.py:ro "$DRILL_WEBUI_IMAGE" /c.py /b/webui.db
   docker exec -i clive-drill-webui python - /app/backend/data/webui.db < /tmp/webui-counts.py
   ```

7. In a **private browser window** (so no live session is reused), open
   `http://localhost:3100`, check the address bar still shows 3100, log in,
   check chats and knowledge bases, and ask a question with a knowledge base
   attached. Confirm in `docker logs clive-ollama` that `/api/embed` calls come
   from the drill container's address
   (`docker inspect clive-drill-webui -f '{{(index .NetworkSettings.Networks "clive-i_default").IPAddress}}'`).
8. Tear down: `$DC down` removes the containers; `$DC down -v` also removes the
   drill volumes. Neither touches the live stack or the backups.

### Full rebuild after losing `sdb` (not drilled)

Everything on `/data` is lost, including Docker's root directory
(`/data/docker`), so all images and the mock volume go with it.

1. Fit the new disk, create one ext4 partition, mount it at `/data`, and update
   `/etc/fstab` with its UUID. Update `deploy/smartd/smartd.conf` with the new
   serial and re-install it (`docs/installation.md` §9).
2. `sudo mkdir -p /data/docker && sudo systemctl restart docker`
   (`docker info --format '{{.DockerRootDir}}'` must print `/data/docker`).
3. Pull the images at the versions in `images.txt`, and pull the models in
   `ollama-models.txt` (`nomic-embed-text`, `qwen2.5-coder:7b`, `llama3.2`)
   once Ollama is up.
4. `.env`: **not in the backup yet** (§7, GPG key deferred). Without a copy,
   recreate it from `.env.example`. New database passwords are fine for a fresh
   restore, because the databases are re-initialised from `.env`.
5. Restore Open WebUI's files into `/data/openwebui_data` (step 4 above, with
   `-v /data/openwebui_data:/dst`), start `postgres` with an empty
   `/data/pgvector_data`, restore the dump into it (step 3 above, into
   `clive-postgres`), then `docker compose up -d`.
6. The Simpro mock database is rebuilt from its seed (`services/simpro_mock/`).
   The six unmounted `/data` directories are restored only if needed, from
   their `data-<dir>.tar.gz` archives.
7. Check as in steps 6 and 7 of the drill, against the live stack.

### Drill report (2026-10-14)

Run on 2026-10-14 from branch `feat/restore-drill` (based on `2cc7a6c`), by
Claude with Alex doing the browser checks. Backup restored:
`~/clive-backups/2026-10-14_1252` (made by `clive-backup.service`).

| Step | Started (BST) | Took | Result |
|---|---|---|---|
| 1. Checksums | 14:01:50 | 1 s | all OK |
| 2. Volumes and `drill-postgres` healthy | 14:01:51 | 8 s | healthy |
| 3. `pg_restore --exit-on-error` | 14:01:59 | under 1 s | exit 0 |
| 4. Open WebUI files and `webui.db` | 14:02:05 | under 1 s | copy's SHA-256 identical to the backup's |
| 5. `drill-webui` healthy | 14:02:27 | 31 s | `{"status":true}`, no migrations run |
| **Commands, checksums to a working Open WebUI** | | **about 68 s** | |
| 7. Browser checks (Alex) | 14:23 | about 3 min | logged in; chats and knowledge base visible; questions answered |

Row counts, Phase 2 database (live, drill, and the backup's own log at 12:52):

```text
public.document_chunk        live 365    drill 365    match
[2026-10-14 12:52:55]       public.document_chunk: 365 rows (matches live)
```

`vector` extension restored at 0.8.6. `webui.db`, backup file against the
drill's copy after Open WebUI had started: all 43 tables match; the non-empty
ones are:

```text
alembic_version      backup 1     drill 1     match
auth                 backup 1     drill 1     match
chat                 backup 11    drill 11    match
chat_file            backup 8     drill 8     match
chat_message         backup 48    drill 48    match
config               backup 341   drill 341   match
feedback             backup 1     drill 1     match
file                 backup 5     drill 5     match
knowledge            backup 1     drill 1     match
knowledge_file       backup 5     drill 5     match
tag                  backup 18    drill 18    match
user                 backup 1     drill 1     match
31 other tables: 0 rows in both
```

These counts were taken before the browser checks. Afterwards the drill had
12 chats: Alex's test question created one in the drill's copy.

Torn down after Alex confirmed (`down -v`): the drill containers, both drill
volumes and the drill network were removed; the six live containers kept
running.

Browser session on the drill (from `docker logs clive-drill-webui`, 13:23–13:26
UTC): `POST /api/v1/auths/signin` 400 then 200, the knowledge base and its
files opened, 3 `POST /api/chat/completions`. Ollama received 13 `/api/embed`
and 11 `/api/chat` calls from the drill's address (the drill container's Docker address), so the
questions were embedded and searched against the restored knowledge base.

**Findings:**

1. **Open WebUI's signing key is not backed up.** The live compose file does
   not set `WEBUI_SECRET_KEY`, so Open WebUI keeps a generated key in
   `/app/backend/.webui_secret_key` inside the container, not on `/data`. The
   drill logged `Generating new WEBUI_SECRET_KEY`. Logging in with the
   password still worked; existing sessions are invalidated, and the same
   happens whenever the live container is recreated. Fixing it means setting
   `WEBUI_SECRET_KEY` in `.env` and `docker-compose.yml` (a live change; not
   done).
2. **The first check was done on the wrong instance.** The first browser
   session after the drill started went to the live Open WebUI (port 3000),
   shown by the logs of both instances and Ollama's caller addresses. Step 7
   now says to use a private window and to confirm in the logs.
3. **Answer quality is not a restore question.** Alex found the answers "not
   exactly on the point" on the live instance as well; it belongs to the
   knowledge base audit (W3) and evaluation set (W4).
4. Two of Claude's ad hoc count commands failed (a Python f-string error and
   `$$` expanded by the shell) and were re-run; the commands above are the
   corrected ones. Neither touched the restore.

## 11. Off-machine copy

Not yet done (W5 T7). Alex closed W5 on 2026-10-16 with this recorded as an
accepted risk in `docs/STATUS.md` (Open risks); no end date set.
