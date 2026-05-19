# GitHub setup (one person per team, ~5 minutes)

## 1. Log in to GitHub (once per machine)

```bash
gh auth login
```

Choose: **GitHub.com** → **HTTPS** → authenticate in browser.

Verify:

```bash
gh auth status
```

## 2. Create the remote repo and push

Run from the project root:

```bash
cd "/Users/linkhitlu/Desktop/CISC 440 Final Project"

gh repo create cisc-440-ust-sustainability-games \
  --public \
  --source=. \
  --remote=origin \
  --description "CISC 440: UST campus sustainability AI games + Monte Carlo" \
  --push
```

**Private repo instead:** add `--private` and drop `--public`.

**Different repo name:** change `cisc-440-ust-sustainability-games` to your team name.

## 3. Invite teammates

On GitHub: **Settings → Collaborators** → add each teammate’s GitHub username.

Or, if using a GitHub Organization, add them to the org team.

## 4. Teammates clone

```bash
git clone https://github.com/YOUR_USERNAME/cisc-440-ust-sustainability-games.git
cd cisc-440-ust-sustainability-games
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Then download Canvas data into `data/` (see [data/README.md](data/README.md)).

## 5. Daily workflow

```bash
git pull                    # before you start
# ... edit code ...
git add src/ report/
git commit -m "Describe your change"
git push
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `remote origin already exists` | `git remote -v` then `git remote set-url origin https://github.com/USER/REPO.git` |
| Push rejected | `git pull --rebase` then `git push` |
| Accidentally committed CSVs | Files in `data/*.csv` are gitignored; if needed: `git rm --cached data/file.csv` |

## Manual alternative (no `gh`)

1. On [github.com/new](https://github.com/new), create an empty repo (no README).
2. Then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git push -u origin main
```
