#!/usr/bin/env python3
"""gemini_imagen_fallback.py — codex /imagen 이 degraded(파일경로 미노출)일 때 쓰는 이미지 생성 fallback.

codex_imagen.sh 가 engine=auto 에서 codex 실패 시 호출한다.
Gemini 이미지 생성 모델(:generateContent, responseModalities=[IMAGE])을 호출해
응답의 inline image bytes 를 TARGET_PATH 에 **그대로** 저장한다(후처리 없음 — NO-CROP 규칙은 슬롯/프롬프트가 책임).

Usage: gemini_imagen_fallback.py <prompt_file.prompt.md> <target_image_path>

백엔드 (2026-06-20):
  IMAGEN_BACKEND=auto(기본)|vertex|aistudio
  - vertex   : ~/.claude/vertex-sa.json SA(빌링) → Vertex AI(us-central1). quota 정상·gemini-2.5-flash-image.
               ⚠️ location=global 은 404, us-central1 만 동작. SA 토큰=gcloud auth print-access-token.
  - aistudio : $GEMINI_API_KEY / ~/.claude/.gemini_api_key (generativelanguage REST).
               ⚠️ OAuth 파생 키(AQ.…)는 이미지 REST quota 0(429) — 6/19 실측. 무료티어 한도 빡셈.
  - auto     : SA(vertex-sa.json) 있으면 vertex 먼저 → 실패 시 aistudio. (free 키 429 상태에선 vertex 가 유일 경로)

비율: 프롬프트에서 'aspect ratio X:Y' / 'X:Y' 를 파싱해 imageConfig.aspectRatio 로 전달(안 주면 모델 기본 1:1).
종료코드: 0 성공 / 1 실패 — 사유를 stderr 로 명확히 남긴다.
"""
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3-pro-image-preview",
    "gemini-2.0-flash-preview-image-generation",
]

# ---- Vertex AI (SA billing) 설정 — gemini_score.py 와 동일 자격 ----
VERTEX_SA = os.path.expanduser(os.environ.get("VERTEX_SA_KEY", "~/.claude/vertex-sa.json"))
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "gen-lang-client-0395149766")
VERTEX_SA_ACCOUNT = os.environ.get(
    "VERTEX_SA_ACCOUNT", "vertex-claude@gen-lang-client-0395149766.iam.gserviceaccount.com")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")  # global 은 이미지 404
GCLOUD_BIN = os.path.expanduser(os.environ.get("GCLOUD_BIN", "~/google-cloud-sdk/bin/gcloud"))
CLOUDSDK_PYTHON = os.environ.get(
    "CLOUDSDK_PYTHON",
    "/Users/jihwan/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12")
# Vertex 에서 이미지 생성 가능한 모델(global 불가 → 리전 엔드포인트)
VERTEX_MODELS = ["gemini-2.5-flash-image"]

_SUPPORTED_RATIOS = {"1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9"}


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
    # 선두 HTML 주석 메타 헤더 제거(codex 메타용) — 실제 이미지 프롬프트만 엔진으로.
    text = re.sub(r"<!--.*?-->", "", text, count=1, flags=re.DOTALL)
    return text.strip()


def parse_aspect(prompt_text):
    """프롬프트에서 종횡비(X:Y)를 추출. 'aspect ratio 3:2' 우선, 없으면 첫 X:Y 토큰."""
    m = re.search(r"aspect\s*ratio[^0-9]{0,12}(\d{1,2}\s*:\s*\d{1,2})", prompt_text, re.I)
    if not m:
        m = re.search(r"\b(\d{1,2}\s*:\s*\d{1,2})\b", prompt_text)
    if not m:
        return ""
    ratio = re.sub(r"\s+", "", m.group(1))
    return ratio if ratio in _SUPPORTED_RATIOS else ""


def _extract_inline_image(data):
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return inline["data"]
    return None


def _gen_config(aspect):
    cfg = {"responseModalities": ["IMAGE"]}
    if aspect:
        cfg["imageConfig"] = {"aspectRatio": aspect}
    return cfg


# ---------------- Vertex (SA billing) ----------------
def vertex_token():
    if not os.path.isfile(VERTEX_SA):
        return ""
    if not os.path.isfile(GCLOUD_BIN):
        log(f"gcloud 없음: {GCLOUD_BIN}")
        return ""
    env = dict(os.environ, CLOUDSDK_PYTHON=CLOUDSDK_PYTHON)
    subprocess.run([GCLOUD_BIN, "auth", "activate-service-account", "--key-file", VERTEX_SA],
                   env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    p = subprocess.run([GCLOUD_BIN, "auth", "print-access-token", "--account", VERTEX_SA_ACCOUNT],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=60)
    t = (p.stdout or "").strip()
    if not t:
        log("vertex 토큰 발급 실패: " + (p.stderr or "")[:160])
    return t


def try_vertex(prompt, target, aspect):
    if not os.path.isfile(VERTEX_SA):
        log("vertex-sa.json 없음 → vertex 건너뜀")
        return False
    tok = vertex_token()
    if not tok:
        return False
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": _gen_config(aspect),
    }).encode()
    for model in VERTEX_MODELS:
        url = (f"https://{VERTEX_LOCATION}-aiplatform.googleapis.com/v1/projects/"
               f"{VERTEX_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/models/"
               f"{model}:generateContent")
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + tok, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            log(f"vertex {model}: HTTP {e.code} {e.read().decode()[:140]}")
            continue
        except Exception as e:
            log(f"vertex {model}: {e}")
            continue
        b64 = _extract_inline_image(data)
        if not b64:
            log(f"vertex {model}: 응답에 inline image 없음")
            continue
        with open(target, "wb") as f:
            f.write(base64.b64decode(b64))
        log(f"OK via vertex/{model} ({VERTEX_LOCATION}, ar={aspect or 'default'}) → {target} "
            f"({os.path.getsize(target)} bytes)")
        return True
    return False


# ---------------- AI Studio (free key) ----------------
def try_aistudio(prompt, target, aspect):
    key = find_key()
    if not key:
        log("GEMINI_API_KEY 없음 ($GEMINI_API_KEY / ~/.claude/.gemini_api_key / ~/.gemini/.env)")
        return False
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": _gen_config(aspect),
    }).encode()
    for model in MODELS:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={key}")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", {}).get("message", "")
            except Exception:
                msg = str(e)
            log(f"aistudio {model}: HTTP {e.code} {msg[:140]}")
            continue
        except Exception as e:
            log(f"aistudio {model}: {e}")
            continue
        b64 = _extract_inline_image(data)
        if not b64:
            log(f"aistudio {model}: 응답에 inline image 없음")
            continue
        with open(target, "wb") as f:
            f.write(base64.b64decode(b64))
        log(f"OK via aistudio/{model} (ar={aspect or 'default'}) → {target} "
            f"({os.path.getsize(target)} bytes)")
        return True
    return False


def main():
    if len(sys.argv) != 3:
        log("usage: gemini_imagen_fallback.py <prompt_file> <target>")
        return 1
    prompt_file, target = sys.argv[1], sys.argv[2]
    if not os.path.isfile(prompt_file):
        log(f"prompt file not found: {prompt_file}")
        return 1
    prompt = load_prompt(prompt_file)
    aspect = parse_aspect(prompt)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)

    backend = os.environ.get("IMAGEN_BACKEND", "auto").strip().lower()
    have_vertex = os.path.isfile(VERTEX_SA)
    if backend == "auto":
        order = (["vertex"] if have_vertex else []) + ["aistudio"]
    elif backend == "vertex":
        order = ["vertex"]
    elif backend == "aistudio":
        order = ["aistudio"]
    else:
        log(f"알 수 없는 IMAGEN_BACKEND={backend} → auto 로 처리")
        order = (["vertex"] if have_vertex else []) + ["aistudio"]

    log(f"backend order={order} aspect={aspect or '(default)'}")
    for be in order:
        ok = try_vertex(prompt, target, aspect) if be == "vertex" else try_aistudio(prompt, target, aspect)
        if ok:
            return 0
    log("모든 백엔드 실패. vertex-sa.json(빌링) 또는 정식 GEMINI_API_KEY 확인 필요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
