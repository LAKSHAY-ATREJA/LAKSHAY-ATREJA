package gateway

import (
	"sync"
	"time"
)

type Breaker struct {
	mu                  sync.Mutex
	failures, threshold int
	openUntil           time.Time
	cooldown            time.Duration
	halfOpen            bool
}

func NewBreaker(threshold int, cooldown time.Duration) *Breaker {
	if threshold < 1 {
		threshold = 1
	}
	if cooldown <= 0 {
		cooldown = time.Second
	}
	return &Breaker{threshold: threshold, cooldown: cooldown}
}

func (b *Breaker) Allow(now time.Time) bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.openUntil.IsZero() {
		return true
	}
	if now.Before(b.openUntil) || b.halfOpen {
		return false
	}
	b.halfOpen = true
	return true
}

func (b *Breaker) Success() {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.failures = 0
	b.openUntil = time.Time{}
	b.halfOpen = false
}

func (b *Breaker) Failure(now time.Time) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.failures++
	if b.failures >= b.threshold {
		b.openUntil = now.Add(b.cooldown)
		b.halfOpen = false
	}
}
