package gateway

import (
	"crypto/rand"
	"encoding/hex"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// Config contains APISentinel's runtime dependencies and resilience controls.
type Config struct {
	Upstream  *url.URL
	Client    *http.Client
	Limiter   *Limiter
	Breaker   *Breaker
	Now       func() time.Time
	RequestID func() string
}

// Gateway is an HTTP resilience gateway for one upstream service.
type Gateway struct {
	upstream  *url.URL
	client    *http.Client
	limiter   *Limiter
	breaker   *Breaker
	now       func() time.Time
	requestID func() string
}

// New creates an HTTP handler. The caller must provide an absolute upstream URL.
func New(config Config) *Gateway {
	client := config.Client
	if client == nil {
		client = &http.Client{Timeout: 3 * time.Second}
	}
	now := config.Now
	if now == nil {
		now = time.Now
	}
	requestID := config.RequestID
	if requestID == nil {
		requestID = randomID
	}
	return &Gateway{upstream: config.Upstream, client: client, limiter: config.Limiter, breaker: config.Breaker, now: now, requestID: requestID}
}

func randomID() string {
	value := make([]byte, 16)
	if _, err := rand.Read(value); err != nil {
		return "unavailable"
	}
	return hex.EncodeToString(value)
}

func (g *Gateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	requestID := r.Header.Get("X-Request-ID")
	if requestID == "" {
		requestID = g.requestID()
	}
	w.Header().Set("X-Request-ID", requestID)
	if r.URL.Path == "/_sentinel/health" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = io.WriteString(w, `{"status":"ok"}`+"\n")
		return
	}
	if g.upstream == nil || g.upstream.Scheme == "" || g.upstream.Host == "" {
		http.Error(w, "gateway upstream is not configured", http.StatusInternalServerError)
		return
	}
	now := g.now()
	clientIP := remoteIP(r.RemoteAddr)
	if g.limiter != nil && !g.limiter.Allow(clientIP, now) {
		http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
		return
	}
	if g.breaker != nil && !g.breaker.Allow(now) {
		http.Error(w, "upstream circuit open", http.StatusServiceUnavailable)
		return
	}
	target := *g.upstream
	target.Path = joinPath(g.upstream.Path, r.URL.Path)
	target.RawPath = ""
	target.RawQuery = joinQuery(g.upstream.RawQuery, r.URL.RawQuery)
	req, err := http.NewRequestWithContext(r.Context(), r.Method, target.String(), r.Body)
	if err != nil {
		http.Error(w, "invalid upstream request", http.StatusBadRequest)
		return
	}
	req.Header = r.Header.Clone()
	removeHopHeaders(req.Header)
	req.Header.Set("X-Request-ID", requestID)
	req.Header.Set("X-Forwarded-For", clientIP)
	req.Host = g.upstream.Host
	resp, err := g.client.Do(req)
	if err != nil {
		if g.breaker != nil {
			g.breaker.Failure(now)
		}
		http.Error(w, "upstream timeout or failure", http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()
	if g.breaker != nil {
		if resp.StatusCode >= http.StatusInternalServerError {
			g.breaker.Failure(now)
		} else {
			g.breaker.Success()
		}
	}
	removeHopHeaders(resp.Header)
	copyHeader(w.Header(), resp.Header)
	w.Header().Set("X-Request-ID", requestID)
	w.WriteHeader(resp.StatusCode)
	_, _ = io.Copy(w, resp.Body)
}

func remoteIP(address string) string {
	host, _, err := net.SplitHostPort(address)
	if err == nil {
		return host
	}
	return address
}

func joinPath(base, path string) string {
	return strings.TrimRight(base, "/") + "/" + strings.TrimLeft(path, "/")
}

func joinQuery(base, request string) string {
	if base == "" {
		return request
	}
	if request == "" {
		return base
	}
	return base + "&" + request
}

func copyHeader(destination, source http.Header) {
	for key, values := range source {
		for _, value := range values {
			destination.Add(key, value)
		}
	}
}

func removeHopHeaders(header http.Header) {
	for _, value := range header.Values("Connection") {
		for _, token := range strings.Split(value, ",") {
			header.Del(strings.TrimSpace(token))
		}
	}
	for _, key := range []string{"Connection", "Keep-Alive", "Proxy-Authenticate", "Proxy-Authorization", "Proxy-Connection", "TE", "Trailer", "Transfer-Encoding", "Upgrade"} {
		header.Del(key)
	}
}
