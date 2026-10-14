# Third-party acknowledgments and notices

This repository is MIT-licensed (see `LICENSE`). We review source licenses before including code; being on GitHub is not itself permission to copy software or game assets.

## Derived code: Seafoodsz/SteamReviewFetch

- Upstream: https://github.com/Seafoodsz/SteamReviewFetch
- Original file: `scripts/steam_reviews_fetcher_v2.py`
- Upstream author / copyright: Copyright (c) 2025 Seafoodsz
- Upstream license: MIT (https://github.com/Seafoodsz/SteamReviewFetch/blob/main/LICENSE)
- Adaptation: `skills/game-opportunity/scripts/adapters/steam_reviews.py` retains the upstream public Steam review request, cursor pagination, ID-based de-duplication and bounded retry patterns, but replaces bulk/raw-file export with rate-bounded, opt-in, in-memory ingestion into a local aggregate and uses Python standard-library HTTP.

MIT License (upstream permission notice)

Copyright (c) 2025 Seafoodsz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Workflow and methodological inspiration (not code copied)

- https://github.com/Abaudat/steam-market-research-skill (MIT, copyright 2026 Adrian Baudat): structured success/failure comparable research. No code or market benchmark tables copied; fixed sales multipliers are **not** inherited.
- https://github.com/AlterLab-IEU/AlterLab_GameForge (MIT, copyright 2026 Cem Ipek, AlterLab Creative Technologies Laboratory): direct/indirect/aspirational peer comparisons and project scope prompts. No source files copied.

Possible future libraries such as jieba, KeyBERT or datasketch are **not bundled dependencies** and should not be represented as installed.
