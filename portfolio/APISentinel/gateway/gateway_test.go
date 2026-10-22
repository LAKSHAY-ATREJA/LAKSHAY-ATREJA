package gateway

import (
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestRateLimiter(t *testing.T) {
	limiter := NewLimiter(1, 2)
	now := time.Unix(100, 0)
	if !limiter.Allow("client", now) || !limiter.Allow("client", now) || limiter.Allow("client", now) {
		t.Fatal("initial burst was not enforced")
	}
	if !limiter.Allow("client", now.Add(time.Second)) {
		t.Fatal("token did not refill")
	}
	if limiter.Allow("client", now.Add(-time.Second)) {
		t.Fatal("a backwards clock must not create a token")
	}
}

func TestRateLimiterConcurrentAccess(t *testing.T) {
	limiter := NewLimiter(1, 10)
	now := time.Unix(100, 0)
	var allowed atomic.Int32
	var group sync.WaitGroup
	for range 50 {
		group.Add(1)
		go func() {
			defer group.Done()
			if limiter.Allow("shared", now) {
				allowed.Add(1)
			}
		}()
	}
	group.Wait()
	if got := allowed.Load(); got != 10 {
		t.Fatalf("allowed %d requests, want 10", got)
	}
}

func TestCircuitBreakerHalfOpenProbe(t *testing.T) {
	breaker := NewBreaker(2, time.Second)
	now := time.Unix(100, 0)
	breaker.Failure(now)
	breaker.Failure(now)
	if breaker.Allow(now) {
		t.Fatal("breaker should be open")
	}
	if !breaker.Allow(now.Add(time.Second)) {
		t.Fatal("breaker should permit one half-open probe")
	}
	if breaker.Allow(now.Add(time.Second)) {
		t.Fatal("breaker should reject a second half-open probe")
	}
	breaker.Success()
	if !breaker.Allow(now.Add(time.Second)) {
		t.Fatal("successful probe should close breaker")
	}
}

func TestHealthDoesNotCallUpstream(t *testing.T) {
	var upstreamCalls atomic.Int32
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		upstreamCalls.Add(1)
		w.WriteHeader(http.StatusTeapot)
	}))
	defer upstream.Close()

	handler := newTestGateway(t, upstream.URL, NewLimiter(10, 10), NewBreaker(2, time.Second), time.Now)
	request := httptest.NewRequest(http.MethodGet, "/_sentinel/health", nil)
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	if response.Code != http.StatusOK || upstreamCalls.Load() != 0 {
		t.Fatalf("health response=%d upstream calls=%d", response.Code, upstreamCalls.Load())
	}
}

func TestGatewayForwardsPathQueryAndCorrelationID(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/base/orders" || r.URL.Query().Get("page") != "2" || r.URL.Query().Get("token") != "demo" {
			t.Errorf("unexpected upstream URL %s", r.URL.String())
		}
		if r.Header.Get("X-Request-ID") != "request-123" || r.Header.Get("X-Forwarded-For") != "192.0.2.1" {
			t.Errorf("missing forwarding headers: %v", r.Header)
		}
		if r.Header.Get("Connection") != "" || r.Header.Get("X-Remove-Me") != "" {
			t.Error("hop-by-hop headers were forwarded")
		}
		w.Header().Set("X-Upstream", "yes")
		w.WriteHeader(http.StatusCreated)
		_, _ = io.WriteString(w, "created")
	}))
	defer upstream.Close()

	handler := newTestGateway(t, upstream.URL+"/base?token=demo", nil, NewBreaker(2, time.Second), time.Now)
	request := httptest.NewRequest(http.MethodPost, "/orders?page=2", nil)
	request.RemoteAddr = "192.0.2.1:1234"
	request.Header.Set("X-Request-ID", "request-123")
	request.Header.Set("Connection", "X-Remove-Me")
	request.Header.Set("X-Remove-Me", "secret")
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	if response.Code != http.StatusCreated || response.Body.String() != "created" {
		t.Fatalf("unexpected response %d %q", response.Code, response.Body.String())
	}
	if response.Header().Get("X-Request-ID") != "request-123" || response.Header().Get("X-Upstream") != "yes" {
		t.Fatalf("missing response headers: %v", response.Header())
	}
}

func TestGatewayCircuitOpensAndRecovers(t *testing.T) {
	var fail atomic.Bool
	fail.Store(true)
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		if fail.Load() {
			http.Error(w, "failure", http.StatusServiceUnavailable)
			return
		}
		_, _ = io.WriteString(w, "recovered")
	}))
	defer upstream.Close()

	now := time.Unix(100, 0)
	handler := newTestGateway(t, upstream.URL, nil, NewBreaker(2, time.Second), func() time.Time { return now })
	for range 2 {
		if code, _ := request(handler, "/api"); code != http.StatusServiceUnavailable {
			t.Fatalf("upstream failure status=%d", code)
		}
	}
	if code, body := request(handler, "/api"); code != http.StatusServiceUnavailable || body != "upstream circuit open\n" {
		t.Fatalf("open circuit response=%d %q", code, body)
	}
	fail.Store(false)
	now = now.Add(time.Second)
	if code, body := request(handler, "/api"); code != http.StatusOK || body != "recovered" {
		t.Fatalf("recovery response=%d %q", code, body)
	}
}

func TestGatewayRateLimit(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer upstream.Close()
	handler := newTestGateway(t, upstream.URL, NewLimiter(0.1, 1), NewBreaker(2, time.Second), func() time.Time { return time.Unix(100, 0) })
	if code, _ := request(handler, "/api"); code != http.StatusNoContent {
		t.Fatalf("first response=%d", code)
	}
	if code, body := request(handler, "/api"); code != http.StatusTooManyRequests || body != "rate limit exceeded\n" {
		t.Fatalf("limited response=%d %q", code, body)
	}
}

func newTestGateway(t *testing.T, target string, limiter *Limiter, breaker *Breaker, now func() time.Time) *Gateway {
	t.Helper()
	upstream, err := url.Parse(target)
	if err != nil {
		t.Fatal(err)
	}
	return New(Config{
		Upstream:  upstream,
		Client:    &http.Client{Timeout: time.Second},
		Limiter:   limiter,
		Breaker:   breaker,
		Now:       now,
		RequestID: func() string { return "generated-id" },
	})
}

func request(handler http.Handler, path string) (int, string) {
	req := httptest.NewRequest(http.MethodGet, path, nil)
	req.RemoteAddr = "192.0.2.10:1234"
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, req)
	return response.Code, response.Body.String()
}
