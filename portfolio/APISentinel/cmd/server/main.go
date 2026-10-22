package main

import (
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"

	"github.com/LAKSHAY-ATREJA/APISentinel/gateway"
)

func envFloat(name string, fallback float64) float64 {
	value, err := strconv.ParseFloat(os.Getenv(name), 64)
	if err != nil || value <= 0 {
		return fallback
	}
	return value
}

func envInt(name string, fallback int) int {
	value, err := strconv.Atoi(os.Getenv(name))
	if err != nil || value <= 0 {
		return fallback
	}
	return value
}

func main() {
	target := os.Getenv("UPSTREAM")
	if target == "" {
		target = "http://127.0.0.1:9090"
	}
	upstream, err := url.Parse(target)
	if err != nil || upstream.Scheme == "" || upstream.Host == "" {
		log.Fatalf("invalid UPSTREAM %q", target)
	}

	timeout := time.Duration(envInt("UPSTREAM_TIMEOUT_MS", 3000)) * time.Millisecond
	cooldown := time.Duration(envInt("BREAKER_COOLDOWN_MS", 10000)) * time.Millisecond
	handler := gateway.New(gateway.Config{
		Upstream: upstream,
		Client:   &http.Client{Timeout: timeout},
		Limiter:  gateway.NewLimiter(envFloat("RATE_PER_SECOND", 10), envFloat("RATE_BURST", 20)),
		Breaker:  gateway.NewBreaker(envInt("BREAKER_THRESHOLD", 3), cooldown),
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	server := &http.Server{
		Addr:              ":" + port,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
	log.Printf("APISentinel listening on %s and forwarding to %s", server.Addr, upstream.Redacted())
	log.Fatal(server.ListenAndServe())
}
