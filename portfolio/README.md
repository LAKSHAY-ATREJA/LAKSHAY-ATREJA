# Software portfolio

Each release includes source, setup instructions, a runnable local demonstration, tests and documented limitations. Publication dates reflect actual releases. Local checks and GitHub-hosted CI are reported separately.

| Project | Current publication status |
| --- | --- |
| [LedgerFlow](LedgerFlow) | Complete implementation released 8 October 2026; 8 tests and real HTTP demo passed locally |
| [Flagship Feature Flags](Flagship-Feature-Flags) | Complete Go implementation released 8 October 2026; race tests, vet, build and real HTTP demo passed locally |
| [OrderMesh](OrderMesh) | Complete Java/Spring implementation released 9 October 2026; credential-free live H2 demo passed |
| [RAGGuard AI Platform](RAGGuard-AI-Platform) | Complete offline-first Python implementation released 10 October 2026; 6 tests and real HTTP demo passed locally |
| [SyncSpace](SyncSpace) | Complete TypeScript/React/WebSocket implementation released 19 October 2026; tests, production build, live demo and visual review passed locally |
| [StreamForge](StreamForge) | Complete Python event-processing reference released 20 October 2026; 5 tests, package build and real HTTP demo passed locally |
| PlatformKit | Queued; Terraform validation still needs resolution |
| APISentinel | Queued for validation and release |
| SearchGrid | Queued for validation and release |
| SLOForge | Queued for validation and release |

LedgerFlow is an in-memory educational reference. Its README explains the scope and provides both an automated demo and an interactive API. Docker configuration is supplied but was not executed during local validation. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37728175826) for the published implementation on Python 3.11 and 3.12.

Flagship Feature Flags is a concurrency-safe, in-memory Go reference service. Its local checks covered race detection, vet, server compilation and live HTTP behaviour for targeting, stable rollout and kill-switch decisions. It has no authentication or persistent/distributed state, and no hosted service or production-scale claim is made. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37731672897) for the published implementation.

OrderMesh demonstrates idempotent order writes and a transactional outbox. A live H2 HTTP demo passed locally using an exact-source packaged artifact. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37917478024) with a fresh Java 17 Maven build, four tests and the end-to-end H2 demo. PostgreSQL, Redpanda and Docker execution are not claimed.

RAGGuard AI Platform is an offline-first RAG reference gateway. Six tests, Ruff checks, compilation and a real loopback HTTP demo passed locally; the demo covered health, deterministic evidence retrieval with citations and prompt-injection rejection. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/38044357761) on Python 3.11 and 3.12 with the locked environment and the same HTTP demo. Its corpus is small and in-memory, its hash-vector retrieval and guardrails are deliberately lightweight, and the optional external model-provider path was not exercised. No hosted service or cloud deployment is claimed.

SyncSpace is an in-memory collaborative task-board reference app. Type checking, two focused tests, a production build and a real two-client WebSocket demo passed locally; desktop and mobile renders were inspected. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/39236560373) with Node 22, the locked dependency graph and the same build and WebSocket demo. It has no authentication, persistence or multi-node coordination, and no hosted service or Docker execution is claimed.

StreamForge is a single-process event-time processing reference. Five tests, Ruff checks, compilation, source and wheel builds, and a real loopback HTTP demo passed locally; the demo covered health, baseline ingestion, anomaly signalling, duplicate rejection and too-late rejection. State and deduplication IDs are in memory, the anomaly rule is a small population-z-score heuristic, and Redpanda, Docker, multi-partition recovery, load testing and hosted deployment were not exercised.

The remaining entries are a release queue, not claims of completed publication. Existing partial folders remain visible until their complete replacements pass their release checks.
