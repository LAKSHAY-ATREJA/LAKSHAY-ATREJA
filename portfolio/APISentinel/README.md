# APISentinel

APISentinel is a compact Go resilience gateway for one HTTP upstream. It combines per-client token-bucket rate limiting, a circuit breaker, upstream timeouts and request correlation in a standard-library-only implementation.

## What it demonstrates

- Thread-safe per-client token buckets with configurable refill rate and burst capacity.
- A circuit breaker that opens after repeated failures and permits one half-open recovery probe after cooldown.
- Upstream request forwarding with path/query preservation, correlation IDs and `X-Forwarded-For`.
- Removal of HTTP hop-by-hop headers in both directions.
- A gateway-owned `/_sentinel/health` endpoint that does not depend on the upstream.
- A credential-free demo using real loopback HTTP servers.

## Requirements

- Go 1.23 or newer.
- No third-party packages, credentials or external services.

## Verify the project

```bash
go test -race ./...
go vet ./...
go build ./cmd/server
go run ./cmd/demo
```

The demo exercises health, request forwarding, correlation IDs, two upstream failures, circuit opening, half-open recovery and a rate-limit rejection.

## Run the gateway

Start any local HTTP service on port 9090, then run:

```bash
UPSTREAM=http://127.0.0.1:9090 PORT=8080 go run ./cmd/server
curl -i http://127.0.0.1:8080/_sentinel/health
curl -i -H 'X-Request-ID: local-demo' http://127.0.0.1:8080/example
```

Configuration:

| Variable | Default | Purpose |
| --- | ---: | --- |
| `UPSTREAM` | `http://127.0.0.1:9090` | Absolute base URL for the single upstream |
| `PORT` | `8080` | Gateway listen port |
| `UPSTREAM_TIMEOUT_MS` | `3000` | Per-request upstream timeout |
| `RATE_PER_SECOND` | `10` | Tokens added per second per client IP |
| `RATE_BURST` | `20` | Maximum stored tokens per client IP |
| `BREAKER_THRESHOLD` | `3` | Consecutive upstream failures before opening |
| `BREAKER_COOLDOWN_MS` | `10000` | Delay before one half-open probe |

## Container image

The included multi-stage Dockerfile builds a small distroless runtime image:

```bash
docker build -t apisentinel .
docker run --rm -p 8080:8080 -e UPSTREAM=http://host.docker.internal:9090 apisentinel
```

The release checks do not claim that this container command was executed.

## Scope and limitations

This is a portfolio/reference implementation, not a production edge gateway. Limiter buckets and breaker state are process-local, in memory and not persisted or shared across replicas. Client identity is the direct peer IP; deployment behind a trusted proxy would require an explicit trusted-proxy policy. There is no authentication, TLS termination, service discovery, load balancing, metrics backend, distributed rate limiting or configuration reload. The in-memory limiter does not evict inactive client keys. Load, fuzz, container and hosted deployment testing are not claimed.

## Author and licence

Lakshay Atreja. Released under the MIT licence. See [LICENSE](LICENSE).

