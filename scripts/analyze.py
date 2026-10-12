import argparse
import ipaddress
import json
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

OUT = Path("reports")
OUT.mkdir(exist_ok=True)


def validate(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise ValueError("Only HTTP(S) URLs are supported")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith((".local", ".internal")):
        raise ValueError("Local hosts are not supported")
    for entry in socket.getaddrinfo(host, None):
        if not ipaddress.ip_address(entry[4][0]).is_global:
            raise ValueError("Non-public network address is not supported")
    return parsed


def website(url):
    response = requests.get(
        url, timeout=20, allow_redirects=False,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/0.1)"},
    )
    if response.is_redirect:
        return {"status": "redirect_not_followed", "location": response.headers.get("Location")}
    response.raise_for_status()
    if "html" not in response.headers.get("Content-Type", "").lower():
        return {"status": "unsupported_content_type"}
    soup = BeautifulSoup(response.text[:2000000], "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    return {"status": "extracted", "title": title,
            "text": " ".join(main.stripped_strings)[:30000],
            "note": "Static HTML only, not an interactive browser review."}


def youtube(url):
    cmd = [sys.executable, "-m", "yt_dlp", "--skip-download",
           "--dump-single-json", "--no-playlist", "--socket-timeout", "15", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode:
            return {"status": "access_failed", "error": result.stderr[-1200:]}
        data = json.loads(result.stdout)
        return {"status": "metadata_only", "title": data.get("title"),
                "uploader": data.get("uploader"), "duration": data.get("duration"),
                "description": (data.get("description") or "")[:12000],
                "subtitle_languages": list((data.get("subtitles") or {}).keys()),
                "automatic_caption_languages": list((data.get("automatic_captions") or {}).keys()),
                "note": "This is not a transcript or visual review of video frames."}
    except (subprocess.TimeoutExpired, ValueError) as exc:
        return {"status": "access_failed", "error": str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    url = parser.parse_args().url
    try:
        parsed = validate(url)
        is_youtube = parsed.hostname.lower() in (
            "youtu.be", "youtube.com", "www.youtube.com", "m.youtube.com")
        result = {"url": url, "type": "youtube" if is_youtube else "website",
                  "data": youtube(url) if is_youtube else website(url)}
    except Exception as exc:
        result = {"url": url, "status": "error", "error": str(exc)}
    (OUT / "report.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    lines = ["# URL analysis", "", "Source: " + url,
             "Type: " + result.get("type", "unknown"),
             "Status: " + result.get("data", {}).get("status", result.get("status", "unknown")),
             "", "## Evidence", "```json",
             json.dumps(result, indent=2, ensure_ascii=False)[:35000],
             "```", "", "## Limitation",
             "Evidence collection only. Metadata does not mean the video was watched."]
    (OUT / "report.md").write_text("\n".join(lines))
    print("Saved reports/report.md and reports/report.json")


if __name__ == "__main__":
    main()
