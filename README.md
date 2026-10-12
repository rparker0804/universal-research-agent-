# Universal Research Agent

A beginner-friendly Codex and GitHub Actions starter to collect evidence from public websites and YouTube URLs.

## First test on mobile
1. Open the **Actions** tab.
2. Choose **Analyze URL** and tap **Run workflow**.
3. Keep the default YouTube URL for the first test.
4. Open the completed run, download the **analysis-report** artifact, and inspect `report.md`.

## What it does
- Public static websites: extracts title and text.
- YouTube: attempts to retrieve metadata and caption-language listings; reports access errors.
- Codex: instructions in `AGENTS.md` and `.agents/skills/analyze-url/SKILL.md` explain how to interpret results.

**Version 1 does not watch video frames, download subtitles, or transcribe audio.** It does not bypass login, DRM, or bot restrictions. Future upgrades can add Whisper, FFmpeg, and Playwright. No API keys are needed for the initial test.

## Run locally
`pip install -r requirements.txt`

`python scripts/analyze.py https://example.com`
