---
name: system-cleanup
description: Find and safely remove redundant files, caches, packages, duplicate apps, old runtimes and leftovers on the user's Mac or Linux machine. Use when the user asks to clean up the system, free disk space, remove unused packages, find what is safe to delete, or remove leftovers after an uninstall or migration.
---

# System cleanup

Report first, remove second. Two phases with a hard stop between them. The scout phase changes nothing on disk: it only reads, lists and runs dry runs.

Per-OS commands, developer caches and measurement caveats live in [`reference.md`](reference.md). Read it before Phase 1.

## Phase 1: scout and report a ranked list

1. Measure: `df -h`, then `du -xhd1` one level at a time into the big folders. On macOS, check the caveats in `reference.md` (Full Disk Access, purgeable space, local snapshots) before you trust the numbers.
   Before you run a tool's CLI, check with `pgrep` that the tool is running. If it is not running, measure its folders with `du` only, because some CLIs start a daemon or VM.
2. List candidates from every section of `reference.md` that applies to this machine: OS packages, app leftovers, developer caches, duplicate apps, Trash, Downloads, old backups, model folders.
3. For each candidate, find what uses it:
   - files: running processes, shell config, launch agents or systemd units, symlinks, last-modified time
   - packages: reverse dependencies, and whether it is part of audio, video, network, display, boot or the desktop session
4. Skip every protected path (below). Mention them in the report only as "kept".
5. Report one table, ranked by reclaimable size, largest first. Within the same size band, rank safer items first.

   | # | item | size | what it is | used by | safe to remove? (yes / regenerates on demand / no) | how to restore |

   Under the table, give the total for the "yes" rows and the total for the "regenerates" rows. Show large user-data folders (documents, media, projects) as "no (user data, review yourself)" and keep them out of both totals.

Phase 1 is done when every candidate has a row and the totals are shown. Stop and wait. The user picks items by number or name.

## Phase 2: remove only what was named

- Files: move to Trash (`/usr/bin/trash` on macOS, `gio trash` on Linux) or a dated quarantine folder, so it is reversible. Permanent deletion only when the user asks.
- Packages: show the dry run first and list every package it pulls with it. Keep any package whose removal takes audio (pipewire, pulseaudio, alsa), video drivers, network manager, display server or bootloader with it, unless the user names that exact package.
- Commands that delete permanently with no dry run (cache clean commands, `journalctl --vacuum-*`, `docker system prune`) count as permanent deletion: run them only after the user approves that exact command.
- Before each removal, re-check that nothing started using it.
- Leave caches that tools need to run (package manager caches, toolchains, virtual environments) unless the user names them, and say what will re-download.
- Write a manifest at `~/cleanup-manifest-<date>.txt`: each moved path with its size and destination, and each removed package with one reinstall command. The user restores everything from this file.
- After cleanup, run smoke checks for anything that could break (sound plays, video plays, network up, the user's main CLIs and apps start) and report space freed.

## Protected paths

Keep these unless the user names the exact path: iCloud Drive (`~/Library/Mobile Documents`), Photos and Mail libraries, Keychains, `~/.ssh`, `~/.gnupg`, password manager data, and agent sessions, configs, memories and credentials. When migrating or removing an app, back up its data first and verify the backup opens.
