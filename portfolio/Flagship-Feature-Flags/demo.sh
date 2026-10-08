#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work_dir="$(mktemp -d)"
port="${PORT:-18080}"
base_url="http://127.0.0.1:${port}"
server_pid=""

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -rf "$work_dir"
}
trap cleanup EXIT

cd "$project_dir"
go build -buildvcs=false -o "$work_dir/flagship" ./cmd/server
PORT="$port" "$work_dir/flagship" >"$work_dir/server.log" 2>&1 &
server_pid=$!

for _ in {1..40}; do
  if curl --fail --silent "$base_url/health" >/dev/null; then
    break
  fi
  sleep 0.1
done
curl --fail --silent "$base_url/health" >/dev/null

curl --fail --silent -X PUT "$base_url/v1/flags" \
  -H 'Content-Type: application/json' \
  -d '{"key":"regional-checkout","enabled":true,"rollout":100,"rules":[{"attribute":"country","operator":"eq","value":"AU"}]}'

au_result="$(curl --fail --silent -X POST "$base_url/v1/evaluate" -H 'Content-Type: application/json' -d '{"key":"regional-checkout","subject":"user-42","context":{"country":"AU"}}')"
us_result="$(curl --fail --silent -X POST "$base_url/v1/evaluate" -H 'Content-Type: application/json' -d '{"key":"regional-checkout","subject":"user-42","context":{"country":"US"}}')"
grep -q '"enabled":true' <<<"$au_result"
grep -q '"enabled":false' <<<"$us_result"

curl --fail --silent -X PUT "$base_url/v1/flags" -H 'Content-Type: application/json' -d '{"key":"regional-checkout","enabled":false,"rollout":100}'
off_result="$(curl --fail --silent -X POST "$base_url/v1/evaluate" -H 'Content-Type: application/json' -d '{"key":"regional-checkout","subject":"user-42","context":{"country":"AU"}}')"
grep -q '"enabled":false' <<<"$off_result"

curl --fail --silent -X PUT "$base_url/v1/flags" -H 'Content-Type: application/json' -d '{"key":"gradual-release","enabled":true,"rollout":50}'
first_rollout="$(curl --fail --silent -X POST "$base_url/v1/evaluate" -H 'Content-Type: application/json' -d '{"key":"gradual-release","subject":"stable-user"}')"
second_rollout="$(curl --fail --silent -X POST "$base_url/v1/evaluate" -H 'Content-Type: application/json' -d '{"key":"gradual-release","subject":"stable-user"}')"
[[ "$first_rollout" == "$second_rollout" ]]

printf 'target AU: %s\n' "$au_result"
printf 'target US: %s\n' "$us_result"
printf 'kill switch: %s\n' "$off_result"
printf 'stable rollout: %s\n' "$first_rollout"
printf 'Flagship demo passed.\n'
