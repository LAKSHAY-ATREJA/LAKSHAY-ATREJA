import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


class ManifestTest(unittest.TestCase):
    def test_kubernetes_resources_and_security_boundaries(self) -> None:
        documents = []
        for path in sorted((ROOT / "k8s/base").glob("*.yaml")):
            documents.extend(yaml.safe_load_all(path.read_text()))

        by_kind = {document["kind"]: document for document in documents}
        self.assertEqual(
            set(by_kind), {"Deployment", "Service", "HorizontalPodAutoscaler"}
        )

        deployment = by_kind["Deployment"]
        pod_spec = deployment["spec"]["template"]["spec"]
        container = pod_spec["containers"][0]
        self.assertTrue(pod_spec["securityContext"]["runAsNonRoot"])
        self.assertFalse(container["securityContext"]["allowPrivilegeEscalation"])
        self.assertEqual(container["securityContext"]["capabilities"]["drop"], ["ALL"])
        self.assertEqual(container["readinessProbe"]["httpGet"]["path"], "/health")
        self.assertIn("requests", container["resources"])
        self.assertIn("limits", container["resources"])

        hpa = by_kind["HorizontalPodAutoscaler"]
        self.assertLess(hpa["spec"]["minReplicas"], hpa["spec"]["maxReplicas"])

    def test_prometheus_rules_have_required_fields(self) -> None:
        rules = yaml.safe_load((ROOT / "monitoring/prometheus-rules.yaml").read_text())
        alerts = [rule for group in rules["groups"] for rule in group["rules"]]
        self.assertEqual(
            {rule["alert"] for rule in alerts}, {"High5xxRate", "LatencyBudgetBurn"}
        )
        for rule in alerts:
            self.assertTrue(rule["expr"])
            self.assertTrue(rule["for"])
            self.assertIn("severity", rule["labels"])
            self.assertIn("summary", rule["annotations"])
