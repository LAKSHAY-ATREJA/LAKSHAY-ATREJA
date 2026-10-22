package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync/atomic"
	"time"

	"github.com/LAKSHAY-ATREJA/APISentinel/gateway"
)

func main() {
	var failing atomic.Bool
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if failing.Load() {
			http.Error(w, "demo upstream failure", http.StatusServiceUnavailable)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		_, _ = fmt.Fprintf(w, "upstream ok path=%s request_id=%s forwarded_for=%s", r.URL.Path, r.Header.Get("X-Request-ID"), r.Header.Get("X-Forwarded-For"))
	}))
	defer upstream.Close()

	target, _ := url.Parse(upstream.URL + "/v1")
	handler := gateway.New(gateway.Config{
		Upstream: target,
		Client:   &http.Client{Timeout: time.Second},
		Limiter:  gateway.NewLimiter(100, 100),
		Breaker:  gateway.NewBreaker(2, 150*time.Millisecond),
	})
	server := httptest.NewServer(handler)
	defer server.Close()

	healthCode, healthBody, _ := get(server.URL+"/_sentinel/health", "")
	assert(healthCode == http.StatusOK && strings.Contains(healthBody, `"status":"ok"`), "health check")

	code, body, requestID := get(server.URL+"/orders?demo=1", "demo-request")
	assert(code == http.StatusOK && strings.Contains(body, "path=/v1/orders") && strings.Contains(body, "request_id=demo-request") && requestID == "demo-request", "forwarding and correlation ID")

	failing.Store(true)
	for range 2 {
		code, _, _ = get(server.URL+"/orders", "")
		assert(code == http.StatusServiceUnavailable, "upstream failure")
	}
	code, body, _ = get(server.URL+"/orders", "")
	assert(code == http.StatusServiceUnavailable && strings.Contains(body, "circuit open"), "open circuit")

	failing.Store(false)
	time.Sleep(175 * time.Millisecond)
	code, body, _ = get(server.URL+"/orders", "")
	assert(code == http.StatusOK && strings.Contains(body, "upstream ok"), "half-open recovery")

	limitedTarget, _ := url.Parse(upstream.URL)
	limited := httptest.NewServer(gateway.New(gateway.Config{
		Upstream: limitedTarget,
		Client:   &http.Client{Timeout: time.Second},
		Limiter:  gateway.NewLimiter(0.01, 1),
		Breaker:  gateway.NewBreaker(2, time.Second),
	}))
	defer limited.Close()
	code, _, _ = get(limited.URL+"/limited", "")
	assert(code == http.StatusOK, "first rate-limited route request")
	code, body, _ = get(limited.URL+"/limited", "")
	assert(code == http.StatusTooManyRequests && strings.Contains(body, "rate limit exceeded"), "rate-limit rejection")

	fmt.Println("APISentinel demo passed: health, forwarding, correlation ID, circuit open/recovery and rate limiting")
}

func get(address, requestID string) (int, string, string) {
	req, _ := http.NewRequest(http.MethodGet, address, nil)
	if requestID != "" {
		req.Header.Set("X-Request-ID", requestID)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, string(body), resp.Header.Get("X-Request-ID")
}

func assert(condition bool, label string) {
	if !condition {
		panic("demo check failed: " + label)
	}
}
