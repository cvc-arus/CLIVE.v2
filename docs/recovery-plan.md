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
| `/data/postgres` | Unknown | Not readable without root |
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
  excluded) and about 900 MB in the unmounted directories.

The directory does not exist yet; it is created when the backup script first
runs (W5 T3).

## 6. Notes for the remaining W5 tasks

Planned, not yet done:

- **Root-owned directories.** `/data/pgvector_data`, `/data/openwebui_data`,
  `/data/open-webui`, `/data/postgres` and `/data/redis` cannot be read by
  `clive`. The backup has to archive them through a container
  (`docker run --rm -v /data/<dir>:/src:ro alpine tar …`, the pattern in the W5
  task file) or with sudo. To be settled in T3.
- **Inventory (T2).** "Source documents" drops out, because `/data/documents`
  is empty and no documents were found stored outside Open WebUI. The six
  unmounted directories are added.
- **`scripts/backup.sh`** defaults to `./backups` inside the repository. That
  directory does not exist, so the script has probably not been run with its
  defaults (a `BACKUP_DIR` override in `.env` was not checked). T3 points it at
  the target above.
- **Ollama.** Models are not backed up; they are re-pulled. `/data/ollama` also
  holds Ollama's identity key (`id_ed25519`), which Ollama recreates if it is
  missing.

## 7. Backup inventory

Not yet done (W5 T2).

## 8. Backup procedure and schedule

Not yet done (W5 T3, T4).

## 9. Disk health baseline

Not yet done (W5 T5).

## 10. Restore procedure and drill report

Not yet done (W5 T6).

## 11. Off-machine copy

Not yet done (W5 T7).
