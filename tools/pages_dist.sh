#!/usr/bin/env bash
# Cloudflare Pages 배포용 폴더(_site) — 사이트에 필요한 파일만 (server/, tests/ 등 제외)
set -e
cd "$(dirname "$0")/.."
rm -rf _site && mkdir _site
for f in index.html feed.json prices.json hexa.json sunday.png favicon.png apple-touch-icon.png; do [ -f "$f" ] && cp "$f" _site/; done
printf '/*\n  Cache-Control: no-cache\n' > _site/_headers
echo "_site: $(ls _site | tr '\n' ' ')"
