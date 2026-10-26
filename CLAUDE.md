# CLAUDE.md

## User

This section is written by the user only. 
This folder is used to serve https://climateorgmap.earth .
When you commit, your name should be model name, version, and effort, e.g.
"Sonnet 5.5 High".
The email should be: `80226974+turibiusrozario@users.noreply.github.com`.
You are heavily sandboxed, so some tools may not be accessible to you.

## AI

Findings from sandbox probing (2026-10-25). Re-verify if something fails; the environment may change.

### Project
- Goal: static site at https://climateorgmap.earth listing its subdomains.
- Repo: https://github.com/turibiusrozario/climateorgmap.earth (public, branch `main`, remote `origin` over HTTPS).
- Host: GitHub Pages, branch-based (`main`, `/`). No build step, so plain HTML/CSS/JS.
- `CLAUDE.md` is tracked (and therefore public). Never put secrets or private notes in it. `.gitignore` only ignores `LLM_*.log`.

### Tools
| Tool | Status | Notes |
|---|---|---|
| git 2.43 | works | Local commits OK |
| gh 2.45 | works | Logged in as `turibiusrozario`; scopes `repo`, `read:org`, `gist`; token in plain text at `~/.config/gh/hosts.yml` |
| network | works | github.com, api.github.com reachable |
| python3 3.12 | works | Local preview: `python3 -m http.server 8000`; also JSON/data generation |
| curl, dig, openssl, rsync | work | Use `dig` / `curl` to verify DNS and the live site |
| node, npm, jq | **missing** | Not needed; avoid |
| ssh key | none | Not needed; HTTPS is used |
| whois | missing | Not needed |

### Git setup (repo-local, no `~/.gitconfig` exists)
- `user.name` = model name + version + effort (e.g. `Sonnet 5.5 High`); the user states the effort level, since Claude can't read it. Update it if the model or effort changes.
- `user.email` = `80226974+turibiusrozario@users.noreply.github.com`.
- `credential.helper` = `!gh auth git-credential`. Without it, HTTPS push fails ("could not read Username").
- Commit messages end with the `Co-Authored-By: Claude ...` trailer given by the harness.
- No `workflow` scope on the token: cannot push `.github/workflows/*`. Don't use GitHub Actions.

### DNS / Pages
- Registrar and DNS: Porkbun (nameservers `*.ns.porkbun.com`). The user manages records; Claude cannot.
- Apex records the user sets (verified against live GitHub Pages DNS):
  - A: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
  - AAAA: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
- The repo needs a `CNAME` file at the root containing exactly `climateorgmap.earth`.
- After DNS propagates: enable Pages (source `main`, `/`), set the custom domain, then tick "Enforce HTTPS" (the certificate can take up to about an hour). Pages can be enabled via `gh api -X POST repos/turibiusrozario/climateorgmap.earth/pages`.
- Other records the user set at Porkbun: `www` CNAME `turibiusrozario.github.io` (correct: GitHub redirects www to the apex once the apex is the custom domain), and `ma` CNAME `nkessel.github.io`.
- As of 2026-10-25 the apex A/AAAA are live at 1.1.1.1, 8.8.8.8 and Porkbun's nameserver. The sandbox's default resolver cached a stale negative answer, so use `dig @1.1.1.1` when checking.
- Live subdomains: only `ma` (https://ma.climateorgmap.earth, "MA Climate Organization Map (MACOM)"), hosted by another GitHub user's Pages repo (`nkessel`), not by this repo.
- Takeover risk: a CNAME to a `*.github.io` host whose repo drops its custom domain can be claimed by anyone. Remove DNS records for dead subdomains, and consider GitHub's Pages domain verification (account Settings > Pages, TXT record at Porkbun).

### Files
- `index.html`: the directory page. It renders `subdomains.json` client-side; preview over `python3 -m http.server`, since `fetch` fails on `file://`.
- `subdomains.json`: the list (`name`, `url`, `description`). Add one entry per live subdomain.
- `CNAME`: `climateorgmap.earth`. Don't delete it.

### Listing subdomains: design constraints
- DNS cannot be enumerated (no zone transfer; wildcard records hide names). The Porkbun API needs keys that Claude doesn't have.
- Source of truth must be a hand-maintained data file, e.g. `subdomains.json` (`name`, `url`, `description`), rendered client-side by `index.html`. Adding a subdomain is then a one-line data edit plus a DNS CNAME record at Porkbun.
- Each subdomain is a separate site, normally its own Pages repo with its own `CNAME` file. This repo only hosts the directory.
- Optional check: a python3 script that `dig`s each listed subdomain and flags dead entries.

