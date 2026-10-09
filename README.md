# RBI Circular Radar

Which new Reserve Bank of India rules apply to you, what to do, and by when. A free tool for fintech
compliance teams: it reads each new RBI notification and says which types of regulated entity it
applies to, whether it requires action, and the dates that matter, each with the exact words and page
from RBI's own document.

- Product requirements: [docs/PRD.md](docs/PRD.md)
- Status: in development. The evaluation runs on real RBI notifications, frozen and labelled before
  any prompt is written; the release gate is recall-first (no applicable notification missed).

Built with Claude Code, after [UPI Triage Agent](https://github.com/AKSHAYKUMARDHAR/UPI-Triage-Agent),
[Is This a Scam?](https://github.com/AKSHAYKUMARDHAR/Is-This-A-Scam) and
[Will My Policy Pay?](https://github.com/AKSHAYKUMARDHAR/Will-My-Policy-Pay).
