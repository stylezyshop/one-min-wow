"""
Downloads free vertical stock video clips from Pexels based on keywords.

Get a free API key at https://www.pexels.com/api/  (no cost, generous limits).
Set it as PEXELS_API_KEY env var / GitHub secret.
"""

import os
import json
import urllib.request
import urllib.parse

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
USER_AGENT = "yt-automation/1.0"


def _headers(api_key=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = api_key
    return headers


def _get(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers=_headers(api_key))
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download(url: str, dest: str) -> None:
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        out.write(resp.read())


def fetch_clips(keywords: list, out_dir: str, clips_needed: int = 4) -> list:
    """
    Downloads up to `clips_needed` vertical video clips matching the
    keywords (round-robins through keywords) and returns local file paths.
    """
    api_key = os.environ["PEXELS_API_KEY"]
    os.makedirs(out_dir, exist_ok=True)

    saved_paths = []
    kw_index = 0

    while len(saved_paths) < clips_needed and kw_index < len(keywords) * 3:
        keyword = keywords[kw_index % len(keywords)]
        kw_index += 1

        url = (
            f"{PEXELS_SEARCH_URL}?query={urllib.parse.quote(keyword)}"
            f"&orientation=portrait&per_page=5"
        )
        try:
            data = _get(url, api_key)
        except Exception as e:
            print(f"Pexels search failed for '{keyword}': {e}")
            continue

        for video in data.get("videos", []):
            # pick the smallest file that's still HD-ish, to keep runtime fast
            files = sorted(
                video.get("video_files", []),
                key=lambda f: f.get("width") or 0,
            )
            candidate = next(
                (f for f in files if (f.get("width") or 0) >= 720), None
            )
            if not candidate:
                continue

            dest = os.path.join(out_dir, f"clip_{len(saved_paths)}.mp4")
            try:
                _download(candidate["link"], dest)
                saved_paths.append(dest)
            except Exception as e:
                print(f"Download failed: {e}")

            if len(saved_paths) >= clips_needed:
                break

    return saved_paths


if __name__ == "__main__":
    paths = fetch_clips(["sunrise", "mountain climb"], "workdir/clips")
    print(paths)
