# System cleanup reference

Scout columns are read-only. Remove columns run only in Phase 2, after the user picks the item.

## Measurement caveats (macOS)

- Without Full Disk Access for the terminal, `du` skips protected folders and reports too little. Say so in the report if totals look low.
- APFS "purgeable" space and Time Machine local snapshots make `df` free space differ from Finder. Check `tmutil listlocalsnapshots /`. macOS frees purgeable space by itself.
- Use `du -xhd1 <dir>` so the scan stays on one volume and one level deep.

## macOS

| candidate | scout | remove |
|---|---|---|
| Homebrew orphans | `brew autoremove --dry-run` | `brew autoremove` |
| Homebrew old versions and cache | `brew cleanup --dry-run` | `brew cleanup` |
| Homebrew top-level formulae | `brew leaves`, `brew list --cask` | `brew uninstall <name>` |
| app caches | `du -xhd1 ~/Library/Caches` | `trash <dir>` |
| app leftovers | `du -xhd1 ~/Library/Application\ Support ~/Library/Containers`, match against installed apps | `trash <dir>` |
| Xcode build data | `du -sh ~/Library/Developer/Xcode/DerivedData` | `trash` its contents |
| Xcode simulators (full Xcode only) | `xcrun simctl list devices unavailable` | `xcrun simctl delete unavailable` |
| local snapshots | `tmutil listlocalsnapshots /` | `tmutil deletelocalsnapshots <date>` |

## Linux

| candidate | scout | remove |
|---|---|---|
| pacman orphans | `pacman -Qdtq` | `pacman -Rsp` dry run, then `pacman -Rs` |
| apt orphans | `apt autoremove --dry-run` | `apt autoremove` |
| reverse dependencies | `pacman -Qi <pkg>` "Required By", `apt-cache rdepends --installed <pkg>` | n/a |
| package dry run | `pacman -Rsp <pkg>`, `apt -s remove <pkg>` | `pacman -Rs`, `apt remove` |
| old kernels | `pacman -Q \| grep linux`, `dpkg -l 'linux-image*'` | via package manager |
| systemd journal | `journalctl --disk-usage` | `journalctl --vacuum-size=<size>` (permanent, no dry run) |
| flatpak runtimes | `flatpak list --runtime` | `flatpak uninstall --unused` |
| snap old revisions | `snap list --all` (rows marked "disabled") | `snap remove <name> --revision=<rev>` |

## Developer caches (both OS)

Package and build caches regenerate on demand. Say what will re-download. Docker is the exception: it holds data.

| tool | scout | remove |
|---|---|---|
| Docker | `docker system df -v`; if the daemon is down, `du -sh ~/.colima ~/Library/Containers/com.docker.docker` and report it as total VM usage, reclaimable unknown, excluded from totals | `docker builder prune` (cache only); `docker image prune` only for images with a verified rebuild or registry source; volumes and containers hold data: back up first (permanent, daemon must run) |
| npm | `du -sh "$(npm config get cache)"` | `npm cache clean --force` |
| pnpm | `du -sh "$(pnpm store path)"` | `pnpm store prune` |
| bun | `du -sh ~/.bun/install/cache` | `trash ~/.bun/install/cache` |
| cargo | `du -sh ~/.cargo/registry ~/.cargo/git` | `trash` those dirs |
| rustup toolchains | `rustup toolchain list` | `rustup toolchain uninstall <name>` |
| go | `du -sh "$(go env GOMODCACHE)"` | `go clean -modcache` |
| uv | `du -sh "$(uv cache dir)"` | `uv cache prune` or `uv cache clean` |
| pip | `du -sh "$(pip3 cache dir)"` | `pip3 cache purge` |
| old `node_modules` | `find ~ -name node_modules -type d -prune -mtime +90` | `trash <dir>` |

## Old app versions (both OS)

Auto-updating tools keep each version in `releases/` or `versions/` with a `current` symlink beside it. Find them with `find ~ -xdev -maxdepth 6 -name current -type l -path '*/packages/*'` and widen the path when needed.

A version folder the symlink does not point to is a candidate, not a "yes". Mark it "yes" only when all three checks pass:

- `pgrep -fl <version-dir>` shows no running process.
- No shell config, launch agent, wrapper symlink or tool config names the folder (`grep -rl <version>` over them).
- The tool's own version marker (for example `auto-update-version`) names the current version.

Remove with `trash <version-dir>`. The tool's updater downloads a version again if it needs one.

## Duplicate apps (macOS)

List bundle IDs in `/Applications`, `~/Applications` and `brew list --cask`. Read each with `mdls -name kMDItemCFBundleIdentifier <app>`. Two apps with the same bundle ID, or one app installed both by cask and by hand, are duplicates. Keep the copy that updates (cask or App Store).

## Duplicate files

`jdupes` and `fdupes` are optional and often not installed. Ask before you install one.
