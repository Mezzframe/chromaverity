# Install and run on macOS, Windows and Linux

chromaverity is plain Python plus the `ffmpeg` and `ffprobe` programs, so it runs anywhere those do. The steps are the same on every system. Only three things change: how you install the tools, how you activate the virtual environment, and how your shell quotes things.

The maintainer works on macOS with Homebrew. Everything in this repo (setup, tests, lint, the zoo, the pre-commit hook) is meant to work the same from Windows and Linux, and CI checks it on all three.

## Where we've actually tested

| System | Status | How we know |
|---|---|---|
| Linux (Ubuntu 22.04, 24.04) | Full test suite passes | Measured: CI on every push (FFmpeg 4.4 and 6.1) |
| macOS | Full test suite passes | Measured: CI on every push (`macos-latest`, Homebrew FFmpeg 9.0), and on the maintainer's Mac (FFmpeg 9.0.2) |
| Windows | Full test suite passes | Measured: CI on every push (`windows-latest`, FFmpeg 9.0 from gyan.dev via Chocolatey). CI runs the test suite in Git Bash, then runs the PowerShell and cmd lines from sections 3 and 4 below, as written. Not tested: Windows PowerShell 5.1 (CI uses PowerShell 7) |
| Windows via WSL2 | Same as Linux ⟨assumption⟩ | WSL2 runs a real Ubuntu, so follow the Linux steps inside it |

Found something that doesn't work on your system? Please [tell us](https://github.com/Novapakt/chromaverity/issues).

## 1. What you need

| Tool | Version | Why |
|---|---|---|
| Python | 3.10 or newer | Runs chromaverity. No other runtime packages needed |
| FFmpeg (`ffmpeg` + `ffprobe`) | 4.4 or newer, built with libx264 | Reads labels, measures pixels. libx264 is only needed to build the test clips |
| Git | any recent | To clone the repo |
| gitleaks | optional, contributors only | The pre-commit hook uses it to block committed secrets |

## 2. Install the tools

### macOS (Homebrew)

```bash
brew install python ffmpeg git gitleaks
```

`brew` is the [Homebrew](https://brew.sh) package manager. Homebrew's `ffmpeg` includes libx264 (measured: the FFmpeg tests run in CI on macOS). If you use pyenv or the python.org installer instead, that's fine too: anything that gives you `python3 --version` of 3.10+.

### Linux

Debian / Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-venv git ffmpeg
```

Fedora: the stock `ffmpeg-free` package leaves out libx264 ⟨verify⟩. chromaverity itself works without it, but the FFmpeg tests will skip. For the full build, enable [RPM Fusion](https://rpmfusion.org) and install `ffmpeg` from there.

```bash
sudo dnf install python3 git ffmpeg-free     # or 'ffmpeg' from RPM Fusion
```

Arch:

```bash
sudo pacman -S python git ffmpeg
```

gitleaks: download a release from [github.com/gitleaks/gitleaks](https://github.com/gitleaks/gitleaks/releases), or use your distro's package if it has one.

### Windows (native)

Open **PowerShell** and use `winget`, the package manager built into Windows 10 and 11:

```powershell
winget install Python.Python.3.13
winget install Gyan.FFmpeg
winget install Git.Git
winget install Gitleaks.Gitleaks     # optional, contributors only
```

Package IDs change now and then ⟨verify with `winget search ffmpeg`⟩. Close and reopen PowerShell afterwards so the new programs are on your `PATH`, then check:

```powershell
python --version
ffmpeg -version
```

If `python` opens the Microsoft Store, Windows is using its placeholder "app execution alias". Turn it off in Settings > Apps > Advanced app settings > App execution aliases, or use the Python launcher `py` instead of `python` in every command below.

### Windows (WSL2)

```powershell
wsl --install            # once, then restart
```

That gives you Ubuntu. Open it and follow the Debian / Ubuntu steps above. Keep your clips inside the Linux filesystem (`~/...`) rather than `/mnt/c/...`: it's much faster ⟨assumption: not measured for chromaverity⟩.

## 3. Get the code and set up

**Where to put it:** a plain local folder such as `~/code` (macOS/Linux) or `C:\code` (Windows). Avoid folders that sync to the cloud (iCloud Desktop & Documents, OneDrive's Desktop/Documents, Dropbox). Sync tools fight with the thousands of small files in `.venv`, and on macOS iCloud breaks the install outright (see Troubleshooting).

The commands are the same everywhere except the line that activates the virtual environment.

**macOS / Linux / WSL (bash or zsh):**

```bash
git clone https://github.com/Novapakt/chromaverity.git
cd chromaverity
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mcp]"
```

**Windows PowerShell:**

```powershell
git clone https://github.com/Novapakt/chromaverity.git
cd chromaverity
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,mcp]"
```

**Windows Command Prompt (cmd.exe):**

```bat
git clone https://github.com/Novapakt/chromaverity.git
cd chromaverity
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev,mcp]"
```

**Git Bash on Windows:** use the bash block, but activate with `source .venv/Scripts/activate`.

What each part does:

| Piece | Meaning |
|---|---|
| `python -m venv .venv` | Run Python's `venv` module (`-m`) to make an isolated environment in a folder called `.venv`. Our packages go there, not into your system Python |
| `source .venv/bin/activate` | Runs the activate script *in your current shell* so `python`, `pip` and `chromaverity` now mean the ones inside `.venv` |
| `.venv\Scripts\Activate.ps1` | The same thing for PowerShell. Windows venvs use `Scripts\` where macOS and Linux use `bin/` |
| `pip install -e ".[dev,mcp]"` | Install this folder (`.`) in editable mode (`-e`), plus the `dev` and `mcp` extras. Quotes stop zsh from treating `[...]` as a filename pattern, and are harmless elsewhere |

You'll see `(.venv)` at the start of your prompt while it's active. Run `deactivate` to leave. Each new terminal needs activating again.

**PowerShell says "running scripts is disabled on this system"?** That's the execution policy. Allow locally created scripts for your user only, once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 4. Try it

With the venv active, these are identical on every system:

```bash
python scripts/make_zoo.py samples
chromaverity inspect samples/full_pixels_labelled_limited.mp4
chromaverity diff samples/good_limited_709.mp4 samples/hop_dropped_tags.mp4
pytest
```

On macOS and Linux `python` inside an active venv is the venv's Python, so `python` and `python3` both work. Forward slashes in paths work on Windows too, for Python and for chromaverity.

If FFmpeg or libx264 is missing, `pytest` still runs the pure tests and marks the FFmpeg ones as skipped. If the summary line says some were skipped, `pytest -rs` lists each skip and its reason (`-r` = report, `s` = skipped). "ffmpeg/ffprobe with libx264 not available" means FFmpeg wasn't found; "PowerShell 7 (pwsh) not installed" is expected on most Macs and Linux machines.

## 5. Contributors: the pre-commit hook

```bash
git config core.hooksPath .githooks
```

This is the same on every system. The hook is a bash script. On Windows, Git for Windows runs it with the bash it ships with, so it works from PowerShell and cmd too ⟨verify⟩. It needs `gitleaks` on your `PATH`, and blocks the commit if it isn't there.

## 6. Pasting the proposed fixes

chromaverity prints fix commands for you to review and run. Shells quote differently, so every fix comes in two versions, and the text output shows the one for your system:

| You're on | Text output shows | JSON field | Paste into |
|---|---|---|---|
| macOS, Linux, WSL | `$ ffmpeg ...` | `command_text` | bash, zsh, Git Bash |
| Windows | `PS> ffmpeg ...` | `command_text_powershell` | PowerShell |

Both are in every JSON report, whatever system made it. Paste the text after `$ ` or `PS> `, not the prompt itself. Quoting is tested in CI by running awkward filenames (spaces, `'`, `$`, commas, `C:\...`) through real PowerShell and checking every argument arrives intact.

**cmd.exe:** we don't print a cmd version. cmd's quoting rules are different again and easy to get wrong. Open PowerShell for fixes (it's the default terminal on Windows 10 and 11), or run `powershell` from cmd first.

The longer commands in our docs wrap lines with `\` at the end. That's bash. In PowerShell use a backtick `` ` `` instead, in cmd use `^`, or put the whole command on one line.

## 7. The MCP server on each system

`chromaverity mcp --root <folder>` is the same everywhere. `~` works in `--root` on every system because chromaverity expands it itself.

The repo's [`.mcp.json`](../.mcp.json) launches `chromaverity` by name, so it only works if Claude Code was started from a terminal where the venv is active. If you see "Executable not found in $PATH: chromaverity", either start `claude` from an activated terminal, or register the server with the full path to the venv's program:

```bash
# macOS / Linux
claude mcp add chromaverity -- /full/path/to/chromaverity/.venv/bin/chromaverity mcp --root ~/Videos/qc-inbox
```

```powershell
# Windows
claude mcp add chromaverity -- C:\full\path\to\chromaverity\.venv\Scripts\chromaverity.exe mcp --root $HOME\Videos\qc-inbox
```

More in [08 Claude Code](08-claude-code.md).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `'ffmpeg' not found on PATH` | FFmpeg isn't installed, or this terminal started before it was | Install it (section 2), then open a new terminal |
| `No module named 'chromaverity'` on macOS, with the venv active | The repo is in a folder synced by iCloud Drive (Desktop & Documents sync). iCloud marks files in the venv "hidden", and recent Python versions skip hidden `.pth` files, which is how the editable install finds the code. Check with `ls -lO .venv/lib/python3.*/site-packages/*.pth` (look for `hidden`). Measured on the maintainer's Mac, 2026-10-14: `chflags nohidden` is undone by iCloud within seconds | Keep code out of iCloud: move the repo to a folder like `~/code`, then delete and recreate `.venv`. Same advice for OneDrive on Windows ⟨assumption: not measured⟩ |
| Pre-commit hook fails on Windows with `bash\r: No such file or directory` | The hook was checked out with Windows line endings (CRLF). Our `.gitattributes` prevents this on fresh clones | `git rm --cached -r . -q` then `git reset --hard` to re-checkout with LF. This discards uncommitted changes, so commit or stash first |
| `zsh: no matches found: .[dev,mcp]` | zsh read the brackets as a filename pattern | Keep the quotes: `".[dev,mcp]"` |
| PowerShell: "running scripts is disabled" | Execution policy | See the note in section 3 |
| `python` opens the Microsoft Store | Windows app execution alias | Turn it off, or use `py` |
| FFmpeg tests all skip | FFmpeg found but without libx264 | Install a build with libx264 (Fedora: RPM Fusion) |
