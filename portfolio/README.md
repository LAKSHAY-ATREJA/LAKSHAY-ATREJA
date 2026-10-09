# Software portfolio

Each release includes source, setup instructions, a runnable local demonstration, tests and documented limitations. Publication dates reflect actual releases. Local checks and GitHub-hosted CI are reported separately.

| Project | Current publication status |
| --- | --- |
| [LedgerFlow](LedgerFlow) | Complete implementation released 8 October 2026; 8 tests and real HTTP demo passed locally |
| [Flagship Feature Flags](Flagship-Feature-Flags) | Complete Go implementation released 8 October 2026; race tests, vet, build and real HTTP demo passed locally |
| [OrderMesh](OrderMesh) | Complete Java/Spring implementation released 9 October 2026; credential-free live H2 demo passed |
| RAGGuard AI Platform | Queued for validation and release |
| SyncSpace | Queued for validation and release |
| StreamForge | Queued for validation and release |
| PlatformKit | Queued; Terraform validation still needs resolution |
| APISentinel | Queued for validation and release |
| SearchGrid | Queued for validation and release |
| SLOForge | Queued for validation and release |

LedgerFlow is an in-memory educational reference. Its README explains the scope and provides both an automated demo and an interactive API. Docker configuration is supplied but was not executed during local validation. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37728175826) for the published implementation on Python 3.11 and 3.12.

Flagship Feature Flags is a concurrency-safe, in-memory Go reference service. Its local checks covered race detection, vet, server compilation and live HTTP behaviour for targeting, stable rollout and kill-switch decisions. It has no authentication or persistent/distributed state, and no hosted service or production-scale claim is made. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37731672897) for the published implementation.

OrderMesh demonstrates idempotent order writes and a transactional outbox. A live H2 HTTP demo passed locally using an exact-source packaged artifact. Fresh Maven verification is delegated to the configured hosted check because the local execution network could not reach Maven Central; this page does not claim that check passed until its result is observed. PostgreSQL, Redpanda and Docker execution are not claimed.

The remaining entries are a release queue, not claims of completed publication. Existing partial folders remain visible until their complete replacements pass their release checks.
