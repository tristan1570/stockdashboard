# Deploy Market Daily

The repository contains a ready-to-serve static site in `public/`. The hosting provider only needs the generated files. The Python updater runs in GitHub Actions. Cloudflare Pages supplies an HTTPS address under `pages.dev`. A stock-data account, OpenAI account and purchased domain are unnecessary for this edition.

## 1. Prepare the GitHub repository

1. Sign in to GitHub and create an empty repository in the intended account. Private visibility works with the Cloudflare GitHub integration. Select a repository you own and review the files being uploaded. The bundled original project brief can remain local.
2. From this project directory, stage the application and its generated demo snapshots using the commands below. Replace `OWNER` and `REPOSITORY` with the actual destination. These initial commands assume an empty remote and a local repository with no existing remote named `origin`. For an existing repository with commits, integrate these files on a branch in its checkout and merge normally.
3. In the GitHub repository, open **Settings → Actions → General**. Enable Actions and allow the scheduled workflow to write repository contents. Branch protection must permit that update path. The test workflow requests read access. Keep billing limits within your intended free allowance.

```sh
git add -- .github .gitignore .env.example README.md requirements.txt scripts tests public docs
git diff --cached --stat
git commit -m "Build the Market Daily demonstration dashboard"
git branch -M main
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

A GitHub personal access token is unnecessary for the workflow. GitHub supplies a short-lived `GITHUB_TOKEN` for its commit. GitHub-hosted standard runners have different allowances for public and private repositories. Check **Account settings → Billing and licensing → Usage** after the first runs. [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

## 2. Create the free Cloudflare Pages site

1. Sign in to Cloudflare and open **Workers & Pages → Create application → Pages → Connect to Git** or **Import an existing Git repository**. Choose the Pages product and the Git integration.
2. Connect the GitHub account, limit access to the dashboard repository, and select it. Choose the project name and production branch `main`. An existing repository can use its default branch if that branch is also the Pages production branch.
3. Select framework preset **None**. Leave the build command empty, leave the root directory at the repository root, and enter **public** as the build output directory. If the form requires a build command, use `exit 0`. No build environment variables or API keys are needed.
4. Select **Save and Deploy**. Open the HTTPS production URL shown by Pages. Confirm that **Demo data** is visible, the three indices load, and the history selector changes the session. The site and its JSON files are public even when the repository is private.

The Pages Free plan lists 500 builds per month. A typical month has roughly 20–23 scheduled trading-session updates. Initial pushes, deploy hooks, preview builds and retries also consume builds. [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) · [Cloudflare Git integration](https://developers.cloudflare.com/pages/configuration/git-integration/)

## 3. Connect production verification

1. Keep **Automatic deployments** enabled for the production branch in Cloudflare Pages. In **GitHub → Settings → Secrets and variables → Actions → Variables**, add a repository variable named `PAGES_URL` containing the production origin. This deployment uses `https://stockdashboard-1bn.pages.dev`. GitHub stores this public address as plain text.
2. Open **Actions → Market data update → Run workflow** on the default branch. For an end-to-end deployment test, select **Publish this run ID to verify that an Actions commit reaches Pages**. GitHub commits a small file containing the run and attempt numbers under `public/data/deployment-check.txt`. The option leaves all market observations intact and defaults to off for routine runs.
3. Inspect the production verification step. It polls the public site for matching SHA-256 digests of the HTML, scripts, styles, latest data, update status, history manifest, latest archive entry and deployment check file when present. The run fails if the deployed release does not match within the verification window. Git integration handles publication without a separate deploy credential.
4. If a different installation needs a fallback and its owner separately approves a persistent external build trigger, the verifier also supports a production `PAGES_DEPLOY_HOOK` stored in **Settings → Secrets and variables → Actions → Secrets**. The stockdashboard deployment uses Git integration.

Scheduled jobs run against the default branch at 23:45 UTC Monday through Friday, which is 6:45 p.m. EST or 7:45 p.m. EDT. GitHub may queue the job. The updater uses the invocation’s Eastern date and the NYSE calendar to decide whether a completed session is available. [Cloudflare deploy hooks](https://developers.cloudflare.com/pages/configuration/deploy-hooks/) · [GitHub schedule semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## 4. Operate and recover

**When a refresh fails.** Open **Actions → Market data update → failed run → update**. Inspect the generation, validation, push and production-verification steps individually. An invalid new session leaves the previous validated snapshot available. A generation failure writes a separate failure status when storage is available. A failed deployment, unavailable runner or Git push failure can prevent that status from reaching visitors. The browser independently shows a stale warning one hour after the next scheduled refresh was due.

**Recovery.** Correct the failing input, repository permissions or deployment settings, then run **Market data update** again on the default branch. Repeated runs reuse an existing validated session and retry production verification even when the data commit is already present. For validation errors, reproduce locally with `python scripts/update_market.py --verify` and `python -m unittest discover -s tests -v`. For missing dates, a manual synthetic seed can reconstruct the 30-session window with `--seed-history` after the current session closes. Keep real vendor data outside this public edition.

**Credentials.** The hosted demo checks its public production URL using read-only HTTP requests. The optional FMP entitlement probe reads `MARKET_DATA_API_KEY` from the local environment. If a future licensed integration uses Actions, add that key through **Settings → Secrets and variables → Actions → Secrets → New repository secret** and pass it only to the authorized provider step. The present workflow does not request it. A vendor key alone cannot establish display or archival rights. [License review](DATA_LICENSE.md)

**iPhone.** Open the production HTTPS address in Safari. Use **Share → Add to Home Screen → Add**. The local loopback URL addresses the device on which the server runs, so use the hosted URL on the phone.

## GitHub Pages backup

A public repository can also serve the same static output with GitHub Pages. Starting from a committed, updated checkout with an `origin` remote, publish the contents of `public/` to a dedicated branch using `git subtree push --prefix public origin gh-pages`. In **Settings → Pages → Build and deployment**, select **Deploy from a branch**, then **gh-pages** and **/(root)**. GitHub displays the project URL after deployment. The dashboard uses relative paths for assets and JSON, so a repository subpath is supported.

This backup is a manual publishing path. Repeat the subtree push from an updated checkout after a new data commit. The supplied production verifier targets Cloudflare Pages. GitHub Pages controls caching and response headers itself.

## Verification record

The shipped example ends on November 17, 2026 and contains 30 validated NYSE sessions. Local Chrome and WebKit tests covered the four ranking combinations, four viewport widths, row details, historical navigation, failed fetches, retry, stale and empty states, and a second simulated scheduled release. The tests used a temporary HTTP-served copy and verified that the new session appeared in the browser. The screenshots capture the synthetic release. [Desktop](screenshots/desktop.png) · [Mobile](screenshots/mobile.png)

The public Pages homepage serves the demo from the public directory. Physical iPhone hardware testing remains separate from WebKit device emulation. Actual market observations remain subject to the provider and licensing review. [API evaluation](API_EVALUATION.md)
