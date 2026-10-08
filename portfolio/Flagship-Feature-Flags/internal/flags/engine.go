package flags

import (
	"crypto/sha256"
	"encoding/binary"
	"errors"
	"sort"
	"strings"
	"sync"
)

type Rule struct {
	Attribute string `json:"attribute"`
	Operator  string `json:"operator"`
	Value     string `json:"value"`
}

type Flag struct {
	Key     string `json:"key"`
	Enabled bool   `json:"enabled"`
	Rollout int    `json:"rollout"`
	Rules   []Rule `json:"rules"`
}

type Context map[string]string

type Engine struct {
	mu    sync.RWMutex
	flags map[string]Flag
}

func New(initial []Flag) *Engine {
	e := &Engine{flags: map[string]Flag{}}
	for _, f := range initial {
		_ = e.Upsert(f)
	}
	return e
}

func (e *Engine) Upsert(f Flag) error {
	if f.Key == "" || f.Rollout < 0 || f.Rollout > 100 {
		return errors.New("flag key and rollout 0..100 are required")
	}
	for _, r := range f.Rules {
		if r.Attribute == "" || (r.Operator != "eq" && r.Operator != "neq" && r.Operator != "prefix") {
			return errors.New("invalid targeting rule")
		}
	}
	e.mu.Lock()
	defer e.mu.Unlock()
	e.flags[f.Key] = f
	return nil
}

func (e *Engine) Snapshot() []Flag {
	e.mu.RLock()
	defer e.mu.RUnlock()
	out := make([]Flag, 0, len(e.flags))
	for _, f := range e.flags {
		out = append(out, f)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Key < out[j].Key })
	return out
}

func (e *Engine) Evaluate(key, subject string, ctx Context) bool {
	e.mu.RLock()
	f, ok := e.flags[key]
	e.mu.RUnlock()
	if !ok || !f.Enabled {
		return false
	}
	for _, r := range f.Rules {
		if !match(r, ctx) {
			return false
		}
	}
	if f.Rollout >= 100 {
		return true
	}
	if f.Rollout <= 0 {
		return false
	}
	h := sha256.Sum256([]byte(key + ":" + subject))
	bucket := int(binary.BigEndian.Uint32(h[:4]) % 100)
	return bucket < f.Rollout
}

func match(r Rule, ctx Context) bool {
	v := ctx[r.Attribute]
	switch r.Operator {
	case "eq":
		return v == r.Value
	case "neq":
		return v != r.Value
	case "prefix":
		return strings.HasPrefix(v, r.Value)
	default:
		return false
	}
}
