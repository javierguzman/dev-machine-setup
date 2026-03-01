# Shortcuts Cheatsheet

> **Legend:** `Prefix` = `Ctrl+a` (tmux) · `<leader>` = `Space` (nvim) · `C-` = Ctrl · `S-` = Shift

---

## Quick Reference — Most Used

### tmux

| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` | Open project picker |
| `Prefix + \|` | Split pane vertically |
| `Prefix + -` | Split pane horizontally |
| `Ctrl+h/j/k/l` | Move between panes |
| `Prefix + m` | Maximize / restore pane |
| `Prefix + [` → `v` → `y` | Copy to system clipboard |

### Neovim — Workflow

| Shortcut | Action |
|----------|--------|
| `Space + F` | Open project picker |
| `Space + e` | Show / hide file tree |
| `Space + ff` | Find file by name |
| `Space + fg` | Search text across all files |
| `42G` or `:42` | Go to line 42 |
| `Space + y` | Copy to system clipboard (paste with Cmd+V anywhere) |

### Neovim — Code Navigation

| Shortcut | Action |
|----------|--------|
| `K` | Show documentation popup |
| `gd` | Peek definition in floating popup — stay in current file |
| `gi` | Jump into implementation |
| `Ctrl+o` | Go back to where you were |
| `gf` | Show all references and definition in a panel |
| `Space + rn` | Rename symbol everywhere |

### Neovim — AI Assistant

| Shortcut | Action |
|----------|--------|
| `Space + aa` | Open AI chat |
| `Space + ae` | Inline edit with AI instruction |
| `Space + ac` | Send selection to chat (visual mode) |

### Window Management

| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+Left/Right` | Cycle between windows |
| `Shift+Alt+m` | Maximize / restore window |
| `Shift+Alt+Left/Right` | Snap to left / right half |

---

## Terminal (zsh)

| Shortcut | Action |
|----------|--------|
| `Alt + Left` / `Alt + Right` | Jump one word backward / forward |
| `Ctrl + A` | Go to beginning of line |
| `Ctrl + E` | Go to end of line |
| `Ctrl + W` | Delete word before cursor |
| `Ctrl + U` | Delete everything before cursor |
| `Ctrl + K` | Delete everything after cursor |
| `Ctrl + L` | Clear screen |
| `Ctrl + R` | Search command history (reverse) |

---

## tmux

### Sessions & Windows

| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` (shell) / `Space+F` (nvim) | Open project picker — fuzzy-find and switch projects |
| `Prefix + c` | New window |
| `Prefix + ,` | Rename current window |
| `Prefix + [1-9]` | Jump to window by number |
| `Prefix + n` / `Prefix + p` | Next / previous window |
| `Prefix + X` | Kill window |
| `Prefix + r` | Reload tmux config |
| `Prefix + i` | Open cheatsheet (tmux-cht.sh) |

### Panes

| Shortcut | Action |
|----------|--------|
| `Prefix + \|` | Split pane vertically (left/right) |
| `Prefix + -` | Split pane horizontally (top/bottom) |
| `Ctrl+h/j/k/l` | Move between panes (and nvim splits) |
| `Prefix + h/j/k/l` | Resize pane |
| `Prefix + m` | Maximize / restore pane (zoom) |
| `Prefix + x` | Kill pane |

### Copy to Clipboard

| Shortcut | Action |
|----------|--------|
| `Prefix + [` | Enter copy mode |
| `v` | Start selection |
| `y` | Copy selection to system clipboard — paste with Cmd+V anywhere |
| `q` | Exit copy mode |

---

## Neovim

### Workflow

| Shortcut | Action |
|----------|--------|
| `Space + F` | Open project picker (tmux-sessionizer) |
| `Space + e` | Toggle file tree (nvim-tree) |
| `Space + ff` | Find files by name (Telescope) |
| `Space + fg` | Search text across all files (live grep) |
| `Space + fs` | Search word under cursor across all files |
| `Space + fb` | List open buffers — switch between open files |
| `Space + fd` | List all diagnostics (errors/warnings) in project |
| `Space + o` | Toggle outline panel — all functions/symbols in file |
| `Space + lg` | Open LazyGit |
| `Space + k` | Toggle kubectl panel |

### AI Assistant (codecompanion.nvim — Claude Sonnet)

| Shortcut | Action |
|----------|--------|
| `Space + aa` | Open / toggle AI chat buffer |
| `Space + ap` | Open action palette — all available AI actions |
| `Space + ae` | Inline AI edit — type a prompt, Claude edits in place |
| `Space + ac` | Add visual selection to the open chat (visual mode) |

**Inside the chat buffer — actions:**

| Shortcut | Action |
|----------|--------|
| `Enter` / `Ctrl+s` | Send message |
| `Ctrl+c` | Close chat |
| `q` | Stop generation |
| `gr` | Regenerate last response |
| `gx` | Clear chat history |
| `gy` | Yank code from response |
| `ga` | Change model / adapter |
| `]]` / `[[` | Jump to next / previous message |
| `?` | Show all available keymaps |

**Context — attach things to your message with `#`:**

| Variable | What it sends |
|----------|---------------|
| `#{buffer}` | Current file contents |
| `#{buffer:filename}` | A specific open buffer by name |
| `#{buffers}` | All open buffers |
| `#{selection}` | Your last visual selection |
| `#{diagnostics}` | LSP errors and warnings in current file |
| `#{diff}` | Current git diff (staged + unstaged) |
| `#{terminal}` | Latest output from terminal buffer |
| `#{viewport}` | Exactly what is visible on screen |

**Slash commands — type `/` in the chat:**

| Command | Action |
|---------|--------|
| `/buffer` | Pick from open buffers and add to chat |
| `/file` | Pick a file from the project and add to chat |
| `/symbols` | Add a tree-sitter outline of a file (functions, classes) |
| `/fetch` | Fetch a URL and add its content to chat |
| `/compact` | Clear message history but keep a summary in context |
| `/help` | Add content from Vim help tags |
| `/now` | Insert current date and time |

> **Workflow — chat about your code:**
> 1. `Space+aa` to open the chat
> 2. Type your question with `#{buffer}` to include the current file
> 3. Add more files with `/file` or `#{buffer:filename}`
> 4. Send with `Enter`, stop with `q`, regenerate with `gr`

> **Workflow — debug with context:**
> 1. `Space+aa` to open chat
> 2. Type your question and include `#{diagnostics}` for LSP errors and `#{diff}` to show recent changes
> 3. Ask Claude to explain or fix

> **Workflow — edit a specific block:**
> 1. Select lines in visual mode (`v` or `V`)
> 2. `Space+ae` — type instruction (e.g. "refactor this to use async/await")
> 3. Claude edits the selection in place
>
> Or: select → `Space+ac` to send to chat first for discussion

> Requires `ANTHROPIC_API_KEY` set in your environment (`~/.zshrc`).

### Go To Line

| Shortcut | Action |
|----------|--------|
| `42G` | Jump to line 42 |
| `:42` + `Enter` | Jump to line 42 (command mode) |
| `gg` | Go to first line |
| `G` | Go to last line |

### LSP — Code Navigation

| Shortcut | Action |
|----------|--------|
| `K` | Hover docs — show documentation popup for symbol under cursor |
| `gd` | **Peek definition** — show implementation in a floating popup *without leaving current file* |
| `gi` | **Go to implementation** — jump into the actual implementation |
| `gD` | Go to declaration |
| `gf` | Find all references + definition in a panel (lspsaga finder) |
| `Ctrl+o` | **Go back** — return to where you were before the last jump |
| `Ctrl+i` | Go forward in jump history |
| `Space + rn` | **Rename symbol** — renames function/variable everywhere it is referenced |
| `Space + ca` | Code actions — quick fixes, imports, refactors |

> **Workflow — inspect without leaving your file:**
> 1. Hover on a function → `K` to read docs
> 2. `gd` to peek the implementation in a popup (press `q` to close — you never moved)
> 3. `gi` to actually jump inside the implementation
> 4. `Ctrl+o` to jump back to where you were

> **Workflow — find all usages:**
> 1. Place cursor on any function or variable
> 2. `gf` to open the finder panel — all references and the definition in one view
> 3. Navigate with `j/k`, press `Enter` to jump to any result

### LSP — Diagnostics

| Shortcut | Action |
|----------|--------|
| `Space + d` | Show diagnostics under cursor |
| `Space + D` | Show all diagnostics for current line |
| `[d` | Jump to previous diagnostic |
| `]d` | Jump to next diagnostic |

### TypeScript / JavaScript (extra)

| Shortcut | Action |
|----------|--------|
| `Space + rf` | Rename file and update all imports |
| `Space + oi` | Organize imports |
| `Space + ru` | Remove unused imports |

### Autocomplete (when menu is open)

| Shortcut | Action |
|----------|--------|
| `Ctrl+j` / `Ctrl+k` | Next / previous suggestion |
| `Ctrl+Space` | Trigger completion manually |
| `Enter` | Confirm selection |
| `Ctrl+e` | Dismiss menu |
| `Ctrl+b` / `Ctrl+f` | Scroll docs up / down |

### Copy & Paste (Clipboard)

| Shortcut | Action |
|----------|--------|
| `Space + y` (visual) | **Copy selection to system clipboard** — paste with Cmd+V in any app |
| `Space + y` (normal) | Copy with motion to system clipboard — e.g. `Space+yy` = line, `Space+yw` = word |
| `y` (normal/visual) | Copy to Vim register only — does NOT go to system clipboard |
| `p` | Paste from Vim register |
| `Space + p` (visual) | Paste over selection without overwriting the register |
| `Space + m` | Paste below current line |

> **To paste into Firefox or any other app:** always use `Space+y` instead of plain `y`.

### Editing

| Shortcut | Action |
|----------|--------|
| `jk` | Exit insert mode (instead of Escape) |
| `J` (visual) | Move selected lines down |
| `K` (visual) | Move selected lines up |
| `Space + x` | Make current file executable (`chmod +x`) |

### Splits & Tabs

| Shortcut | Action |
|----------|--------|
| `Space + sv` | Split vertically |
| `Space + sh` | Split horizontally |
| `Space + se` | Equalize split sizes |
| `Space + sx` | Close split |
| `Space + sm` | Maximize / restore split |
| `Ctrl+h/j/k/l` | Navigate between splits (and tmux panes) |
| `Space + to` | Open new tab |
| `Space + tx` | Close tab |
| `Space + tn` / `Space + tp` | Next / previous tab |

### Telescope (inside picker)

| Shortcut | Action |
|----------|--------|
| `Ctrl+j` / `Ctrl+k` | Move down / up in results |
| `Ctrl+q` | Send selected results to quickfix list |
| `Enter` | Open selected result |
| `Esc` | Close picker |

---

## Window Management (Yabai + skhd)

### Focus

| Shortcut | Action |
|----------|--------|
| `Ctrl + Alt + Right` | Focus next window |
| `Ctrl + Alt + Left` | Focus previous window |
| `Alt + s` | Focus left display |
| `Alt + g` | Focus right display |

### Window Size

| Shortcut | Action |
|----------|--------|
| `Shift + Alt + m` | Maximize / restore toggle |
| `Shift + Alt + Left` | Snap to left half |
| `Shift + Alt + Right` | Snap to right half |
| `Shift + Alt + e` | Balance all windows equally |
| `Shift + Ctrl + h/l` | Resize window left / right |
| `Shift + Ctrl + k/j` | Resize window up / down |

### Move Windows

| Shortcut | Action |
|----------|--------|
| `Shift + Alt + h/j/k/l` | Swap window with neighbor in direction |
| `Ctrl + Alt + h/j/k/l` | Warp (move and split) in direction |
| `Shift + Alt + s` | Move window to left display |
| `Shift + Alt + g` | Move window to right display |
| `Shift + Alt + p` / `Shift + Alt + n` | Move window to prev / next space |
| `Shift + Alt + [1-7]` | Move window to space number |

### Other

| Shortcut | Action |
|----------|--------|
| `Shift + Alt + t` | Toggle window float |
| `Shift + Alt + r` | Rotate layout clockwise |
| `Ctrl + Alt + r` | Restart yabai |
| `Ctrl + Alt + q` / `Ctrl + Alt + s` | Stop / start yabai |
