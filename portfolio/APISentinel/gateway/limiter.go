package gateway

import (
	"sync"
	"time"
)

type bucket struct {
	tokens float64
	last   time.Time
}
type Limiter struct {
	mu          sync.Mutex
	rate, burst float64
	buckets     map[string]*bucket
}

func NewLimiter(rate, burst float64) *Limiter {
	if rate <= 0 {
		rate = 1
	}
	if burst < 1 {
		burst = 1
	}
	return &Limiter{rate: rate, burst: burst, buckets: map[string]*bucket{}}
}

func (l *Limiter) Allow(key string, now time.Time) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	b, ok := l.buckets[key]
	if !ok {
		b = &bucket{tokens: l.burst, last: now}
		l.buckets[key] = b
	}
	elapsed := max(0, now.Sub(b.last).Seconds())
	b.tokens = min(l.burst, b.tokens+elapsed*l.rate)
	if now.After(b.last) {
		b.last = now
	}
	if b.tokens < 1 {
		return false
	}
	b.tokens--
	return true
}
