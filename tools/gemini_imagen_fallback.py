#!/usr/bin/env python3
"""gemini_imagen_fallback.py — codex /imagen 이 degraded(파일경로 미노출)일 때 쓰는 이미지 생성 fallback.

codex_imagen.sh 가 engine=auto 에서 codex 실패 시 호출한다.
GEMINI_API_KEY 로 Gemini 이미지 생성 모델(:generateContent, responseModalities=[IMAGE])을 호출해
응답의 inline image bytes 를 TARGET_PATH 에 **그대로** 저장한다(후처리 없음 — NO-CROP 규칙은 슬롯/프롬프트가 책임).

Usage: gemini_imagen_fallback.py <prompt_file.prompt.md> <target_image_path>
키 출처(우선순위): $GEMINI_API_KEY → ~/.claude/.gemini_api_key → ~/.gemini/.env(GEMINI_API_KEY=...)
종료코드: 0 성공 / 1 실패(키없음·quota·모델없음·이미지없음) — 사유를 stderr 로 명확히 남긴다.

⚠️ 알려진 제약(2026-06-19 실측): OAuth 파생 키(AQ.…)는 generativelanguage REST 이미지 생성에
   quota 0(429)일 수 있다. 그 경우 정직하게 1 로 실패하고, AI Studio 발급 정식 키가 필요함을 알린다.
"""
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error

MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3-pro-image-preview",
    "gemini-2.0-flash-preview-image-generation",
]


def log(m):
    print(f"[gemini_fallback] {m}", file=sys.stderr)


def find_key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    home = os.path.expanduser("~")
    p = os.path.join(home, ".claude", ".gemini_api_key")
    if os.path.isfile(p):
        with open(p) as f:
            k = f.read().strip()
        if k:
            return k
    p = os.path.join(home, ".gemini", ".env")
    if os.path.isfile(p):
        with open(p) as f:
            for line in f:
                m = re.match(r"\s*GEMINI_API_KEY\s*=\s*(.+)\s*$", line)
                if m:
                    return m.group(1).strip().strip('"').strip("'")
    return ""


def load_prompt(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # 선두 HTML 주석 메타 헤더 제거(codex 메타용) — 실제 이미지 프롬프트만 Gemini 로.
    text = re.sub(r"<!--.*?-->", "", text, count=1, flags=re.DOTALL)
    return text.strip()


def main():
    if len(sys.argv) != 3:
        log("usage: gemini_imagen_fallback.py <prompt_file> <target>")
        return 1
    prompt_file, target = sys.argv[1], sys.argv[2]
    if not os.path.isfile(prompt_file):
        log(f"prompt file not found: {prompt_file}")
        return 1
    key = find_key()
    if not key:
        log("GEMINI_API_KEY 없음 ($GEMINI_API_KEY / ~/.claude/.gemini_api_key / ~/.gemini/.env)")
        return 1
    prompt = load_prompt(prompt_file)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()

    last_err = ""
    for model in MODELS:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={key}")
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", {}).get("message", "")
            except Exception:
                msg = str(e)
            last_err = f"{model}: HTTP {e.code} {msg[:140]}"
            log(last_err)
            continue
        except Exception as e:
            last_err = f"{model}: {e}"
            log(last_err)
            continue

        # 응답에서 inline image 추출
        b64 = None
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    b64 = inline["data"]
                    break
            if b64:
                break
        if not b64:
            last_err = f"{model}: 응답에 inline image 없음"
            log(last_err)
            continue

        with open(target, "wb") as f:
            f.write(base64.b64decode(b64))
        log(f"OK via {model} → {target} ({os.path.getsize(target)} bytes)")
        return 0

    log(f"모든 모델 실패. 마지막 오류: {last_err}")
    log("OAuth 파생 키는 이미지 REST quota 0(429)일 수 있음 → AI Studio 정식 API 키 필요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
