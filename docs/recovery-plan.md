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
| `sda` | `sda2` | `/` | 228G (160G free) | OS, the repository (`<repo-dir>`), **backups** |
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

**`<home>/clive-backups/`**, on `sda2` (decided 2026-10-14, Alex).

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
| 7 | Image versions | — | Each running image's digest saved to a text file | `open-webui:main` and `ollama/ollama` are unpinned tags, so a restore could pull a newer Open WebUI that migrates `webui.db`. Running: Open WebUI 0.11.0 |

Not backed up:

- **`simpro-mock-db`:** disposable test data, rebuilt from the seed script
  (`docs/installation.md` §9).
- **Source documents:** none outside Open WebUI (`/data/documents` is empty).
- **Git repository:** on GitHub; no bundle.

**Sensitivity:** backups contain customer documents (item 3) and chats
(item 2). The backup directory is to be readable by `clive` only (mode 700),
and the off-machine copy (§11) is to be encrypted.

## 8. Backup procedure and schedule

`scripts/backup.sh` (W5 T3, 2026-10-14). Run it from anywhere; it is not
scheduled yet (W5 T4).

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
come from the containers' own environment.

**Outstanding (Alex):**

- `.env` still has the Phase 2 values `BACKUP_DIR=./backups` and
  `BACKUP_RETENTION_DAYS`. Set `BACKUP_DIR=<home>/clive-backups` and remove
  `BACKUP_RETENTION_DAYS`. Until then the target has to be passed on the command
  line: `BACKUP_DIR=<home>/clive-backups ./scripts/backup.sh`.
- Create the GPG key pair and set `BACKUP_GPG_RECIPIENT` (deferred, 2026-10-14):

  ```bash
  gpg --quick-generate-key "CLIVE backup <<email>>" rsa4096 encr never
  gpg --list-keys --with-colons "CLIVE backup" | awk -F: '/^fpr/{print $10; exit}'
  gpg --export-secret-keys --armor <FPR> > <off-machine media>/clive-backup-private.asc
  gpg --delete-secret-keys <FPR>
  ```

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
[2026-10-14 11:42:34] Backup complete: <home>/clive-backups/2026-10-14_1141 (830M)
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

Retention was tested separately against 80 empty dummy folders (two a day for
40 days) in a scratch directory: it kept 10 (the last 7 days plus the Sundays
2026-09-20, 09-27 and 10-04; 10-11 is both) and left a `.partial` folder alone.

## 9. Disk health baseline

Not yet done (W5 T5).

## 10. Restore procedure and drill report

Not yet done (W5 T6).

## 11. Off-machine copy

Not yet done (W5 T7).
