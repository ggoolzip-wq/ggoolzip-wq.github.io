#!/usr/bin/env bash
# 초대 비밀번호 바꾸기: bash set-site-pass.sh   (비밀번호를 물어봄, 화면에 안 보임)
#   한 줄로: printf '%s' "ggoolzip-invite:새비밀번호" | sha256sum | cut -d' ' -f1 | npx wrangler secret put SITE_PASS_HASH
# 바꾸면 기존 기기의 '초대 확인'은 무효(새 로그인 때 새 비밀번호 필요). 이미 로그인한 기기는 그대로 사용 가능.
set -euo pipefail
cd "$(dirname "$0")"
if [ -z "${SITE_PASS:-}" ]; then read -rsp '새 초대 비밀번호: ' SITE_PASS; echo; fi
P="$(printf '%s' "$SITE_PASS" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
[ -n "$P" ] || { echo '비밀번호가 비었습니다'; exit 1; }
mkdir -p "$HOME/.config/ggoolzip"; ( umask 077; printf '%s' "$P" > "$HOME/.config/ggoolzip/SITE_PASS" )
printf '%s' "ggoolzip-invite:$P" | sha256sum | cut -d' ' -f1 | npx wrangler secret put SITE_PASS_HASH
echo '완료: SITE_PASS_HASH 갱신 (비밀번호 사본: ~/.config/ggoolzip/SITE_PASS)'
