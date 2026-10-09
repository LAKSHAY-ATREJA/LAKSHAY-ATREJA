#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
port="${PORT:-18081}"
base_url="http://127.0.0.1:${port}"
work_dir="$(mktemp -d)"
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
if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  mvn -B package
fi
jar_path="${JAR_PATH:-target/ordermesh-1.0.0.jar}"
if [[ ! -f "$jar_path" ]]; then
  printf 'OrderMesh jar not found: %s\n' "$jar_path" >&2
  exit 1
fi

java -jar "$jar_path" --spring.profiles.active=demo --server.port="$port" >"$work_dir/server.log" 2>&1 &
server_pid=$!

for _ in {1..100}; do
  if curl --fail --silent "$base_url/health" >/dev/null; then
    break
  fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    cat "$work_dir/server.log" >&2
    exit 1
  fi
  sleep 0.1
done
curl --fail --silent "$base_url/health" >/dev/null

create_order() {
  curl --fail --silent -X POST "$base_url/v1/orders" \
    -H 'Content-Type: application/json' \
    -H 'Idempotency-Key: demo-order-1' \
    -d '{"customerId":"demo-customer","amount":19.99}'
}

first="$(create_order)"
second="$(create_order)"
first_id="$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$first")"
second_id="$(sed -n 's/.*"id":"\([^"]*\)".*/\1/p' <<<"$second")"
[[ -n "$first_id" && "$first_id" == "$second_id" ]]

fetched="$(curl --fail --silent "$base_url/v1/orders/$first_id")"
grep -q '"customerId":"demo-customer"' <<<"$fetched"
grep -q '"status":"PENDING"' <<<"$fetched"

conflict_status="$(curl --silent --output "$work_dir/conflict.json" --write-out '%{http_code}' \
  -X POST "$base_url/v1/orders" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-order-1' \
  -d '{"customerId":"demo-customer","amount":29.99}')"
[[ "$conflict_status" == "400" ]]

printf 'created: %s\n' "$first"
printf 'idempotent retry: %s\n' "$second"
printf 'fetched: %s\n' "$fetched"
printf 'conflicting retry status: %s\n' "$conflict_status"
printf 'OrderMesh demo passed.\n'
