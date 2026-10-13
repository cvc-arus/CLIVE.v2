# W5 — Backups and Restore Drill

| | |
|---|---|
| **Template** | Full (changes data handling and the host) |
| **Status** | Approved |
| **Depends on** | W6 T1 (`STATUS.md` exists) |
| **Related** | Phase 2 `scripts/backup.sh`, recovery plan |

## 1. Goal

Reliable, scheduled backups of everything needed to rebuild CLIVE, stored on a
different physical disk from the data, proven by a restore drill.

## 2. Business value

The machine has two non-RAID SSDs. A single disk failure today could lose the
knowledge base, Open WebUI users and chats, and all Phase 3 databases. A tested
backup turns that from a project-ending event into a few hours of restore work.

## 3. Tasks

### T1 — Find where CLIVE's data physically lives (read-only)
Current layout reported by Alex:

| Device | Mount | Size | Used |
|---|---|---|---|
| `/dev/sda2` | `/` | 228G | 56G |
| `/dev/sdb1` | `/data` | 229G | 14G |

Alex's initial idea was to back up to `sda2` (`/`). **That only protects against
disk failure if CLIVE's data lives on `sdb1`.** Docker's default data directory
(`/var/lib/docker`) is on `/`, so if volumes are there, backups must go to `/data`
instead.

Steps (all read-only):
1. Docker root directory and the device it sits on.
2. Every named volume and bind mount used by the Compose stack, with its host path.
3. Map each to `sda2` or `sdb1`.
4. Record the result in the recovery plan and choose the backup target: **the
   disk that does not hold the data.** If data is split across both disks,
   stop and agree a layout with Alex.

**Stop point:** table of volume → host path → disk, and the proposed target.

### T2 — Backup inventory
| Item | Method | Notes |
|---|---|---|
| Postgres databases (Phase 2 instance: Open WebUI, pgvector; `simpro-mock-db`) | `pg_dump -Fc` per database + `pg_dumpall --globals-only` | Logical dumps are consistent while running |
| Open WebUI data volume (uploads, config) | `tar` of the volume, read-only mount | |
| Source documents (if stored outside Open WebUI) | `rsync` | Confirm location in T1 |
| `.env` files | Encrypted archive (`gpg --symmetric`) | Passphrase stored outside the machine |
| Git repository | Already in remote? If not, include a `git bundle` | Confirm with Alex |
| Ollama models | **Not backed up**; record `ollama list` output | Re-pullable |
| Docker Compose files, configs | Covered by git | |

Confirm the list against T1 findings. **Stop point:** final inventory.

### T3 — Backup script
Update `scripts/backup.sh` (or create it) to:
1. Write to `<target>/clive-backups/<YYYY-MM-DD_HHMM>/`.
2. Dump each database, archive volumes, encrypt `.env`, write the model list.
3. Write a `MANIFEST.txt` with file sizes and SHA-256 checksums.
4. Apply retention: keep 7 daily and 4 weekly (Sunday) backups.
5. Exit non-zero and log clearly on any failure; never print secrets.
6. Read secrets from container environments or `.env`, never hard-coded.

**Stop point:** run once manually; show the backup folder listing and manifest.

### T4 — Schedule [needs approval: host change]
A systemd timer (preferred) or cron entry running the script daily at a quiet
hour, logging to the journal. Show the unit files before installing.
**Stop point:** `systemctl list-timers` shows the timer.

### T5 — Disk health monitoring [needs approval: host package]
Install `smartmontools` on the host (justified exception to Docker-first: it
needs direct hardware access). Check both disks' health and record the
baseline. Enable `smartd` email or journal alerts as agreed with Alex.
**Stop point:** health output for both disks.

### T6 — Restore drill
1. Restore the latest backup into a **separate** Compose project name and
   separate volumes; never over the live stack.
2. Start the restored stack on different ports.
3. Verify: log in to Open WebUI, see existing chats and knowledge base, ask a
   question that uses the knowledge base; check row counts in each database
   match the live system at backup time.
4. Record the time taken and every manual step in the recovery plan.
5. Tear down the drill stack (**confirm with Alex before removing its volumes**).

**Stop point:** drill report.

### T7 — [HUMAN] Off-machine copy
Decide and obtain an off-machine target (NAS or external drive). Until then,
record in `STATUS.md` → Open risks: "No off-machine backup — accepted until <date>".

## 4. Implementation notes

- Logical database dumps (`pg_dump`) instead of copying Postgres data
  directories: consistent without stopping containers and portable across
  minor versions.
- Backups run on the host because they need `docker` and both disks.
- A cross-disk copy protects against one disk failing. It does **not** protect
  against theft, fire, accidental `rm`, or ransomware, because both disks are
  in the same, always-mounted machine. Hence T7.

## 5. Commands

Discovery (T1):
```bash
docker info --format '{{.DockerRootDir}}'
df -h "$(docker info --format '{{.DockerRootDir}}')"
docker volume ls
docker volume inspect $(docker volume ls -q) --format '{{.Name}} {{.Mountpoint}}'
docker compose config | grep -A3 -E 'volumes:|source:'
lsblk -f
findmnt /data
```

Database dump pattern (T3), secrets taken from the container's own environment:
```bash
docker compose exec -T <pg-service> sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > "$DEST/<db>.dump"
docker compose exec -T <pg-service> sh -c 'pg_dumpall -U "$POSTGRES_USER" --globals-only' > "$DEST/<instance>-globals.sql"
```

Volume archive pattern:
```bash
docker run --rm -v <volume>:/src:ro -v "$DEST":/dst alpine tar czf /dst/<volume>.tgz -C /src .
```

Disk health (T5):
```bash
sudo apt install smartmontools
sudo smartctl -H /dev/sda
sudo smartctl -H /dev/sdb
```

## 6. Configuration

New `.env` variables (names only): `BACKUP_TARGET_DIR`, `BACKUP_RETENTION_DAILY`,
`BACKUP_RETENTION_WEEKLY`. Encryption passphrase is **not** stored on the machine.

## 7. Folder structure

```
scripts/
├── backup.sh
└── restore.sh            # T6, if useful to script
deploy/systemd/           # unit files kept in git, installed to /etc/systemd/system
├── clive-backup.service
└── clive-backup.timer
<target>/clive-backups/   # outside the repo
```

## 8. Files created / modified

`scripts/backup.sh`, `scripts/restore.sh` (optional), `deploy/systemd/*`,
`.env.example`, recovery plan, backup strategy doc, `STATUS.md`, `CHANGELOG.md`.

## 9. Verification

- Backup folder contains every inventory item and a manifest with checksums.
- `sha256sum -c MANIFEST.txt` passes.
- Timer listed and one scheduled run succeeds (check `journalctl -u clive-backup`).
- Restore drill succeeds; row counts match.
- `smartctl -H` reports PASSED on both disks.

## 10. Rollback procedure

- Script: `git revert`.
- Timer: `sudo systemctl disable --now clive-backup.timer`, remove the unit files.
- `smartmontools`: `sudo apt remove smartmontools`.
- Backups themselves are never deleted as part of rollback.

## 11. Common issues

| Issue | Fix |
|---|---|
| Backup target on the same disk as data | Re-check T1; target must be the other disk |
| `pg_dump` version mismatch | Run `pg_dump` inside the database container (as above), not on the host |
| Permission denied writing to `/data` | Create the backup directory owned by the user running the timer |
| Timer runs but script fails silently | Script must exit non-zero; check `journalctl` |
| Restore collides with live stack | Use a different Compose project name, volume names and ports |

## 12. Documentation updates

Backup strategy, recovery plan (including drill report), installation guide
(timer setup), `.env.example`, `STATUS.md`, `CHANGELOG.md`.

## 13. Git commit

`feat(backup): scheduled cross-disk backups with checksums and restore drill`

## 14. Acceptance criteria

- [ ] Data location per disk documented; backup target is the other disk
- [ ] Every inventory item backed up, with checksummed manifest
- [ ] Daily schedule running; retention applied
- [ ] Disk health baseline recorded for both disks
- [ ] Restore drill completed and documented with time taken
- [ ] Off-machine copy in place, or recorded as an accepted risk with a date
