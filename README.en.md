# BioBrain · Hermes Plugin

Brings the [BioBrain](https://github.com/Satyr-Astry/biobrain) bionic cognitive architecture into Hermes Desktop — **7 brain tools** plus a live status panel in the right pane.

> **Hard rule**: the brain runs **standalone**. It never replaces the Hermes main-session model (which would squeeze VRAM and freeze the gateway).

## Tools

| Tool | Emoji | Description |
|------|-------|-------------|
| `brain_ask` | 🧠 | ★ Ask the brain: recalls neural memory → language area expresses it |
| `brain_distill` | 📚 | ★ Autonomous distillation: outline → learn point by point → self-check → store |
| `brain_recall` | 🔍 | Search memory to see what it knows |
| `brain_teach` | ✍️ | Teach one Q&A pair directly |
| `brain_think` | 💭 | Pure thinking stream (activation spread, no language area) |
| `brain_sleep` | 😴 | Sleep consolidation (merge plasticity, prune weak links) |
| `brain_state` | 📊 | Brain status (neurons / activation / memory / language area) |

## Status Panel

The right pane shows live state: neural organisation (neurons / tracts / groups / active / ticks), tier residency, self-model (good at / weak at / success rate), and learning state (experience buffer / REM candidates / collective layer / newborns / robustness). Buttons: **Think / Sleep / Refresh**.

## Installation

1. Drop `bio-brain/` into your Hermes plugin directory:

   ```
   $HERMES_HOME/plugins/bio-brain/
   ├── plugin.yaml
   ├── __init__.py
   ├── tools.py
   └── desktop/plugin.js
   ```

2. Point the plugin at your brain code. Resolution order (first match wins):

   | # | Source | Example |
   |---|--------|---------|
   | 1 | Env var `BIOBRAIN_PATH` (or `HERMES_BIOBRAIN_PATH`) | `BIOBRAIN_PATH=E:\BIONIC_AI\code` |
   | 2 | `brain/` subdirectory inside the plugin | bundled brain |
   | 3 | `plugins.bio-brain.brain_path` in `config.yaml` | see below |

   ```yaml
   # $HERMES_HOME/config.yaml
   plugins:
     bio-brain:
       brain_path: "E:\\BIONIC_AI\\code"
   ```

   The directory is accepted if it contains `conductor.py`. No local paths are hardcoded — nothing leaks if unset.

3. Restart the Hermes gateway / desktop app and enable `bio-brain` under `plugins.enabled`.

## Dependencies

The brain itself needs only `numpy`; `brain_distill` requires a working LLM language area (configured on the brain side).

## Notes

- The brain loads **lazily as a singleton**, avoiding repeated construction.
- Memory is persisted to `<brain dir>/agent_memory.json`; it is written back after `brain_teach` / `brain_distill` / `brain_sleep`.
- `_NEURONS` defaults to 8192 (16K takes ~30 s per turn — 8K feels more responsive).

## License

MIT —— applies to this plugin (the `bio-brain/` directory). Note that this repository does **not** bundle the brain itself: the BioBrain core is a separate project licensed under **CCSAL-1.0** (see [Satyr-Astry/biobrain](https://github.com/Satyr-Astry/biobrain)). When redistributing the brain together with this plugin, both licences apply.
