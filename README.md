# arkan

arkan is pstack under the name arkan: its skills, playbooks and agents, copied from [pstack](https://github.com/cursor/plugins/tree/c742dd6/pstack) at commit `c742dd6`. only three names differ: `arkan-mode`, `arkan-help` and `arkan-agent`.

## install

arkan is a plugin for omp and claude code. in omp:

```
/marketplace add IsrafilEMIN/arkan
/marketplace install arkan@arkan
/reload-plugins
```

in claude code:

```
/plugin marketplace add IsrafilEMIN/arkan
/plugin install arkan@arkan
```

to update in omp, run `/marketplace update arkan`, then `/marketplace upgrade arkan@arkan`, then `/reload-plugins`.

for any other harness, link or copy each folder in [`skills/`](skills/) into the folder it reads skills from.

## what differs from pstack

- the names `poteto-mode`, `poteto-help` and `poteto-agent` are `arkan-mode`, `arkan-help` and `arkan-agent`, in file names and in text.
- the two files in [`agents/`](agents/) keep pstack's prompt and use omp's frontmatter: no `is_background`, and `arkan-agent` loads `arkan-mode` through `autoloadSkills`.
- arkan adds two skills, `good-css` and `simplest-path`, and the plugin files in `.claude-plugin/`.
- arkan leaves out pstack's `assets/`, `automations/`, `docs/` and its own `README.md`. `arkan-help` still links to the guide and the claude code adapter in `docs/`, and those links lead nowhere.

the text still names cursor tools, paths and model slugs.

## sources

[`NOTICE`](NOTICE) lists the project each copied skill comes from and keeps the license text of each source. [`docs/resources/`](docs/resources/) has one file for each article that shaped arkan.
