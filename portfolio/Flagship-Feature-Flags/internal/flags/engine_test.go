package flags

import "testing"

func TestStableRollout(t *testing.T) {
	e := New([]Flag{{Key: "new-ui", Enabled: true, Rollout: 25}})
	a := e.Evaluate("new-ui", "user-42", nil)
	for i := 0; i < 100; i++ {
		if e.Evaluate("new-ui", "user-42", nil) != a {
			t.Fatal("rollout must be deterministic")
		}
	}
}

func TestRuleAndKillSwitch(t *testing.T) {
	e := New([]Flag{{Key: "beta", Enabled: true, Rollout: 100, Rules: []Rule{{Attribute: "country", Operator: "eq", Value: "AU"}}}})
	if !e.Evaluate("beta", "1", Context{"country": "AU"}) {
		t.Fatal("expected targeted user")
	}
	if e.Evaluate("beta", "2", Context{"country": "US"}) {
		t.Fatal("expected non-targeted user to be excluded")
	}
	if err := e.Upsert(Flag{Key: "beta", Enabled: false, Rollout: 100}); err != nil {
		t.Fatal(err)
	}
	if e.Evaluate("beta", "1", Context{"country": "AU"}) {
		t.Fatal("kill switch must win")
	}
}

func TestRejectsInvalidRule(t *testing.T) {
	e := New(nil)
	if e.Upsert(Flag{Key: "x", Enabled: true, Rollout: 50, Rules: []Rule{{Attribute: "tier", Operator: "contains", Value: "pro"}}}) == nil {
		t.Fatal("expected validation error")
	}
}
