#!/usr/bin/env python3
"""Generate OpenAI image assets for clinic handouts.

The script writes a local image file that can be referenced from HTML with a
relative <img> path. It intentionally uses the OpenAI Image API over raw HTTPS
so fresh clones do not need an extra Python package beyond the existing build
requirements.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://api.openai.com/v1/images/generations"
DEFAULT_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
DEFAULT_STYLE = """Create a clean, patient-friendly medical illustration for an A4 Korean clinic handout.
Style: premium hospital patient education infographic, accurate but non-scary, warm white background, restrained navy/steel-blue/green accents, soft lighting, clear empty space for HTML labels.
Do not include patient names, chart numbers, dates of birth, logos, watermarks, UI, letters, numbers, or any readable text inside the image."""


def infer_format(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    suffix = path.suffix.lower().lstrip(".")
    if suffix == "jpg":
        return "jpeg"
    if suffix in {"jpeg", "png", "webp"}:
        return suffix
    return "png"


def make_payload(args: argparse.Namespace, output_format: str) -> dict[str, object]:
    prompt = args.prompt.strip()
    if args.raw_prompt:
        final_prompt = prompt
    else:
        final_prompt = f"{DEFAULT_STYLE}\n\nSubject and composition:\n{prompt}"

    payload: dict[str, object] = {
        "model": args.model,
        "prompt": final_prompt,
        "size": args.size,
        "quality": args.quality,
        "output_format": output_format,
        "n": 1,
    }
    if args.background:
        payload["background"] = args.background
    if output_format in {"jpeg", "webp"} and args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    return payload


def call_openai(payload: dict[str, object], api_key: str) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def write_sidecar(output: Path, payload: dict[str, object], response: dict[str, object] | None) -> None:
    sidecar = output.with_suffix(output.suffix + ".prompt.json")
    record = {
        "api": "OpenAI Image API",
        "model": payload.get("model"),
        "size": payload.get("size"),
        "quality": payload.get("quality"),
        "background": payload.get("background"),
        "output_format": payload.get("output_format"),
        "prompt": payload.get("prompt"),
    }
    if response and isinstance(response.get("usage"), dict):
        record["usage"] = response["usage"]
    sidecar.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a local OpenAI image asset for clinic HTML handouts.",
    )
    parser.add_argument("--prompt", required=True, help="Visual subject/composition. Do not include patient identifiers.")
    parser.add_argument("--output", required=True, help="Output path, usually shared/assets/generated/<slug>.png")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Image model. Default: {DEFAULT_MODEL}")
    parser.add_argument("--size", default="1536x1024", choices=("1024x1024", "1536x1024", "1024x1536", "auto"))
    parser.add_argument("--quality", default="medium", choices=("low", "medium", "high", "auto"))
    parser.add_argument("--background", choices=("transparent", "opaque", "auto"), default="auto")
    parser.add_argument("--output-format", choices=("png", "jpeg", "webp"), default=None)
    parser.add_argument("--output-compression", type=int, choices=range(0, 101), metavar="0-100")
    parser.add_argument("--raw-prompt", action="store_true", help="Use --prompt verbatim without the clinic style wrapper.")
    parser.add_argument("--dry-run", action="store_true", help="Print the request payload and do not call the API.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output_format = infer_format(output, args.output_format)
    payload = make_payload(args, output_format)

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set. Export it before generating image assets.", file=sys.stderr)
        return 2

    try:
        response = call_openai(payload, api_key)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"OpenAI Image API failed ({exc.code}): {body}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"OpenAI Image API request failed: {exc}", file=sys.stderr)
        return 1

    items = response.get("data")
    if not isinstance(items, list) or not items:
        print("OpenAI Image API response did not include data[0].", file=sys.stderr)
        return 1
    b64 = items[0].get("b64_json")
    if not isinstance(b64, str):
        print("OpenAI Image API response did not include data[0].b64_json.", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(b64))
    write_sidecar(output, payload, response)
    print(f"Wrote {output.relative_to(ROOT)}")
    print(f"Wrote {output.with_suffix(output.suffix + '.prompt.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
