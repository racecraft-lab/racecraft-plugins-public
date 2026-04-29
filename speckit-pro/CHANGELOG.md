# Changelog

## [1.9.1](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.9.0...speckit-pro-v1.9.1) (2026-04-29)


### Bug Fixes

* **autopilot:** archive sweep runs actual cleanup on feature branches instead of always dry-running; dry-run is reserved for main and protected integration branches ([c614fab](https://github.com/racecraft-lab/racecraft-plugins-public/commit/c614fab09f19c877a4c0b69ea0a9fb02d2fc11b4))

## [1.9.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.8.0...speckit-pro-v1.9.0) (2026-04-28)

### Features

* **speckit-pro:** add archive sweep support ([e489dac](https://github.com/racecraft-lab/racecraft-plugins-public/commit/e489dac719081c577c7131dc49f8287ceb633f7b))
* **autopilot:** start archive-aware runs with Archive Sweep before Phase 0
* **coach:** add guidance for installing or vendoring the Racecraft archive extension
* **status:** surface archive extension state, excluded current spec, and cleanup safety

## [1.8.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.7.1...speckit-pro-v1.8.0) (2026-04-26)


### Features

* **codex:** support GPT-5.5 subagents ([e5a363a](https://github.com/racecraft-lab/racecraft-plugins-public/commit/e5a363a3023c587a0800175fc3f7b766d6bf516e))


### Bug Fixes

* **codex:** harden autopilot fallback guards ([c68d5a4](https://github.com/racecraft-lab/racecraft-plugins-public/commit/c68d5a405841af9ce8d6e3c72c95bb740ee5b4f1))

## [1.7.1](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.7.0...speckit-pro-v1.7.1) (2026-04-11)


### Bug Fixes

* **codex:** align skill packaging with official docs ([5e4f502](https://github.com/racecraft-lab/racecraft-plugins-public/commit/5e4f50227660b8e5b3aaef8de5d80fc991aece34))
* **codex:** restore bundled agent install flow ([be7a500](https://github.com/racecraft-lab/racecraft-plugins-public/commit/be7a5008f1b21f52c71aa1ab59c3b08f0f465181))
* **codex:** restore bundled agent install flow ([f02a025](https://github.com/racecraft-lab/racecraft-plugins-public/commit/f02a0252909c855646d841ee38e75232793602ba))

## [1.7.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.6.0...speckit-pro-v1.7.0) (2026-04-11)


### Features

* **codex:** add optional spark autopilot helper ([a696327](https://github.com/racecraft-lab/racecraft-plugins-public/commit/a6963279711a4a79160c7bb9dec27a2d342268f8))

## [1.6.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.5.1...speckit-pro-v1.6.0) (2026-04-11)


### Features

* **codex:** install official custom subagents ([230586b](https://github.com/racecraft-lab/racecraft-plugins-public/commit/230586b0c99a9be7913077fd4cbf6837a27327d0))


### Bug Fixes

* **codex:** align marketplace contract with official docs ([6b56879](https://github.com/racecraft-lab/racecraft-plugins-public/commit/6b56879fbd41aead04ce1863014791bf450b6c89))

## [1.5.1](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.5.0...speckit-pro-v1.5.1) (2026-04-11)


### Bug Fixes

* harden Codex autopilot progress contract ([c9fa2c5](https://github.com/racecraft-lab/racecraft-plugins-public/commit/c9fa2c502ae8aba05ea5fa3db504923076139bd0))
* **skills:** harden codex autopilot progress contract ([8b69738](https://github.com/racecraft-lab/racecraft-plugins-public/commit/8b6973870c1790e8e49a5027dbf0829b7d20af40))

## [1.5.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.4.0...speckit-pro-v1.5.0) (2026-04-08)


### Features

* **codex:** align speckit plugin entrypoints ([9a6b619](https://github.com/racecraft-lab/racecraft-plugins-public/commit/9a6b619584d89316310639effb52a7d39581099f))


### Bug Fixes

* address PR review comments for actionable errors and safety checks ([1d72b2d](https://github.com/racecraft-lab/racecraft-plugins-public/commit/1d72b2de609ec17974d23f01bc1a3af0ecbab6cc))
* **codex:** split platform-specific eval runners ([64decd1](https://github.com/racecraft-lab/racecraft-plugins-public/commit/64decd1cd246759780c591fcf4e242f9db182a6f))
* remediate PR review findings — dead code, docs, and test gaps ([72bd2af](https://github.com/racecraft-lab/racecraft-plugins-public/commit/72bd2afe7452a08d2d8ac731bc406c08c093dda2))
* remediate PR review findings across evals, docs, and dead code ([3f8c665](https://github.com/racecraft-lab/racecraft-plugins-public/commit/3f8c66581ea78bd89e31b211ef17d6827b127827))
* **speckit-pro:** align Codex entrypoints with skills ([b46ff83](https://github.com/racecraft-lab/racecraft-plugins-public/commit/b46ff83de03cce20f21ce519ce88d03a158a44da))

## [1.4.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.3.0...speckit-pro-v1.4.0) (2026-04-08)


### Features

* **speckit-pro:** add Codex CLI commands for all 5 entry points ([9ecaee5](https://github.com/racecraft-lab/racecraft-plugins-public/commit/9ecaee5df49b5e34073000048bbef58bf0aa2efd))

## [1.3.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.2.0...speckit-pro-v1.3.0) (2026-04-08)


### Features

* **speckit-pro:** add Codex CLI agent definitions with model mapping ([9545bd0](https://github.com/racecraft-lab/racecraft-plugins-public/commit/9545bd050d0f6217fc8330a8e7083aa83b8eb9fb))
* **speckit-pro:** add Codex CLI autopilot skill with shared references and scripts ([2caf3eb](https://github.com/racecraft-lab/racecraft-plugins-public/commit/2caf3ebddb7f51e8a1f4daf18944433701bc367d))
* **speckit-pro:** add Codex CLI coach skill with shared references ([7e6ee96](https://github.com/racecraft-lab/racecraft-plugins-public/commit/7e6ee96cc33a8709590d2e02dbf79b3ba1d981e3))
* **speckit-pro:** add Codex CLI plugin manifest and marketplace registry ([2a1bac2](https://github.com/racecraft-lab/racecraft-plugins-public/commit/2a1bac271c29c2d8d032ca403d02be1e17e316b3))
* **speckit-pro:** add Codex CLI SessionStart hook ([57c1f08](https://github.com/racecraft-lab/racecraft-plugins-public/commit/57c1f08401fa54d5ff261cc79408f01f09d93ed0))
* **speckit-pro:** add OpenAI Codex CLI compatibility ([14cba27](https://github.com/racecraft-lab/racecraft-plugins-public/commit/14cba270ff5652b2759a20890fd259c5b441abb2))


### Bug Fixes

* **speckit-pro:** address PR review — set -e safety, CLAUDE_PLUGIN_ROOT, CC-only agents ([b3c6a03](https://github.com/racecraft-lab/racecraft-plugins-public/commit/b3c6a033148cebeb27515a540609cccd2bd80bc8))
* **speckit-pro:** address PR review — x_high reasoning effort, CC-only paths, CC-only flags ([225876b](https://github.com/racecraft-lab/racecraft-plugins-public/commit/225876b410dd1d30e31e60f85ecebf2ef00dae09))

## [1.2.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.1.0...speckit-pro-v1.2.0) (2026-04-04)


### Features

* **SPEC-004:** implement sentinel job, verification checklist, CLAUDE.md CI/CD docs ([98faa10](https://github.com/racecraft-lab/racecraft-plugins-public/commit/98faa102a4e83a25c4fe39c761a4b1a5fc8be6a4))
* **SPEC-004:** Integration & Verification — branch protection, Copilot review, CI/CD docs ([f710ffb](https://github.com/racecraft-lab/racecraft-plugins-public/commit/f710ffbbb09a6bbb7b1e2f2d78004b4b3055d93a))
* **SPEC-005:** add skill trigger quality spec to technical roadmap ([66b7251](https://github.com/racecraft-lab/racecraft-plugins-public/commit/66b725168b43820d7776da3c47f52c1d9e0a7648))


### Bug Fixes

* **SPEC-004:** configure git user in test fixtures for CI ([bf4f10d](https://github.com/racecraft-lab/racecraft-plugins-public/commit/bf4f10d78e1467e3fa331da1fdcea389fc481bb5))
* **SPEC-004:** remediate code review findings for PR [#5](https://github.com/racecraft-lab/racecraft-plugins-public/issues/5) ([3f76fab](https://github.com/racecraft-lab/racecraft-plugins-public/commit/3f76fab72c98203708b3f2d20ad72e83ea283152))
* **speckit-pro:** resolve plugin script paths in autopilot SKILL.md ([1bf3d01](https://github.com/racecraft-lab/racecraft-plugins-public/commit/1bf3d01a04d98783448174233cfa600b76e0f236))
* **speckit-pro:** resolve plugin script paths in autopilot SKILL.md ([27ce64e](https://github.com/racecraft-lab/racecraft-plugins-public/commit/27ce64e684ea0e6524100ffc36ad348b46111517))

## [1.1.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v1.0.0...speckit-pro-v1.1.0) (2026-04-04)


### Features

* **autopilot:** add constitution validation step and prerequisites checks for workflow execution ([bb49d74](https://github.com/racecraft-lab/racecraft-plugins-public/commit/bb49d747580460dbf3fffe167b729061ca269876))
* **autopilot:** add setup command for spec preparation and workflow generation ([f723b5d](https://github.com/racecraft-lab/racecraft-plugins-public/commit/f723b5d95ecacbc77e62441f963f73fdda361269))
* **autopilot:** enhance clarify session handling with interactive prefixes and detailed integration testing guidelines ([38b300b](https://github.com/racecraft-lab/racecraft-plugins-public/commit/38b300bbcce0482dc2099a956a1b5cbf04833896))
* **autopilot:** enhance documentation for command invocation and phase execution details ([4091e99](https://github.com/racecraft-lab/racecraft-plugins-public/commit/4091e99de7b5fd8fcd76534b1b738a15a620bc2a))
* **autopilot:** enhance execution rules for persistent tool calls and clarify command usage ([3945971](https://github.com/racecraft-lab/racecraft-plugins-public/commit/3945971769373546c20b3b54c2f394b75d921436))
* **autopilot:** enhance gap remediation and analysis processes with detailed research steps and consensus mechanisms ([d0445b4](https://github.com/racecraft-lab/racecraft-plugins-public/commit/d0445b4c74c401454339e490c12af7075092d1ed))
* **autopilot:** enhance phase execution documentation with granular task creation and execution rules ([62746f7](https://github.com/racecraft-lab/racecraft-plugins-public/commit/62746f7206e83dd0d489d7e3bbb9add10713c216))
* **autopilot:** remove context enrichment setting and update documentation for workflow prompts ([ca703ac](https://github.com/racecraft-lab/racecraft-plugins-public/commit/ca703acf2145b74122f1709f32b0640f6075c462))
* **autopilot:** simplify allowed-tools to a wildcard for broader compatibility ([e9ff654](https://github.com/racecraft-lab/racecraft-plugins-public/commit/e9ff654d207e73b0b73314a88c04856e9b4dc9d7))
* **autopilot:** update execution rules to enforce copy-paste prompts and eliminate context enrichment ([c35d2a2](https://github.com/racecraft-lab/racecraft-plugins-public/commit/c35d2a2b74b54ca1b5402729083ba3cdc08feacb))
* **autopilot:** update phase execution rules and enhance gate validation for comprehensive findings remediation ([ba2d432](https://github.com/racecraft-lab/racecraft-plugins-public/commit/ba2d4326ca4397d5d9174500152fb174ebc583f1))
* **skills:** Optimized skills using the /skill-creator eval framework ([381f73b](https://github.com/racecraft-lab/racecraft-plugins-public/commit/381f73bd678a7d610add12b422658e35c1853ef4))
* **speckit-pro:** add release-please config and marketplace sync script ([86f3b7e](https://github.com/racecraft-lab/racecraft-plugins-public/commit/86f3b7e31d2a6cadc100f4b74e6bd6370452b510))
* **speckit-pro:** remediate subagent review findings and rename master plan to technical roadmap ([12c8c1c](https://github.com/racecraft-lab/racecraft-plugins-public/commit/12c8c1c00cc786709413dfd1325bb684be7355a0))
* **status:** enhance project roadmap details and unify dashboard presentation ([6d1481f](https://github.com/racecraft-lab/racecraft-plugins-public/commit/6d1481f33794c4a618211f20ec939899faf2b896))
* **status:** enhance status command to provide full project roadmap and next-spec recommendations ([beb3bb1](https://github.com/racecraft-lab/racecraft-plugins-public/commit/beb3bb1be62c53f373c670cba0c9e1ba1252abd4))
* **status:** update status dashboard to recommend next spec based on priority and dependencies ([79c4ee3](https://github.com/racecraft-lab/racecraft-plugins-public/commit/79c4ee302e96f621dcd4b1fd16cbee4f11a1e582))


### Bug Fixes

* **agents:** resolved workflow bugs with the agents. ([27184c1](https://github.com/racecraft-lab/racecraft-plugins-public/commit/27184c178a902a36b793860235f1cbaee26a8e2e))
* **speckit-pro:** address pre-merge review findings ([448363e](https://github.com/racecraft-lab/racecraft-plugins-public/commit/448363e0b9ea823164d554dd41fc4dc4e8509c55))
* **speckit-pro:** address pre-merge review findings ([256786a](https://github.com/racecraft-lab/racecraft-plugins-public/commit/256786a0e7e916967a3df822bab54ca9eab77a26))
* **speckit-pro:** address RepoPrompt review findings ([fe58271](https://github.com/racecraft-lab/racecraft-plugins-public/commit/fe582712ff833d1e702bfd6d5e4e380542c8ddf5))
* **speckit-pro:** address RepoPrompt review findings ([e2d7acc](https://github.com/racecraft-lab/racecraft-plugins-public/commit/e2d7accbe5fec5e0dd935aaaaea7ff668dbbc154))
* **speckit-pro:** replace stale omnifocus-mcp project reference in run-all.sh ([768ccd6](https://github.com/racecraft-lab/racecraft-plugins-public/commit/768ccd644b94ad0ea739c1f4c46bef74516ad1bf))
