# Software portfolio

Each release includes source, setup instructions, a runnable local demonstration, tests and documented limitations. Publication dates reflect actual releases. Local checks and GitHub-hosted CI are reported separately.


## Project priorities and levels

These levels rank what to show first for graduate software/backend/cloud roles. They reflect visible technical depth, relevance, and evidence in the repositories—not production deployment. For a specific application, promote the matching AI, data, or computer-vision project from Level A or B.

### Level A — Lead with these

| Priority | Project | Best short description |
|---:|---|---|
| 1 | [DevTrack API](https://github.com/LAKSHAY-ATREJA/devtrack-api) | JWT-authenticated Node.js/Express API with user-scoped records, validation, filtering, pagination, aggregate statistics, automated tests, and a Docker demo. |
| 2 | [OrderMesh](OrderMesh) | Java 17/Spring Boot order-service reference demonstrating idempotent writes and a transactional outbox, with a runnable H2 demo and verified tests. |
| 3 | [PlatformKit](PlatformKit) | Terraform AWS foundation plus Kubernetes/Helm examples with autoscaling, health probes, and Prometheus alerts; credential-free demo and CI checks, with no cloud deployment claimed. |
| 4 | [SignalOps](https://github.com/LAKSHAY-ATREJA/SignalOps-Cloud-Service-Health-Incident-Detection-API) | Async FastAPI telemetry and incident service with rolling anomaly baselines, severity classification, database persistence, Docker support, tests, and CI. |
| 5 | [StreamForge](StreamForge) | Python event-time processing reference with windows, watermarks, deduplication, late-event rejection, and anomaly signals; single-process state with a runnable HTTP demo. |
| 6 | [APISentinel](APISentinel) | Go resilience gateway with per-client token-bucket limits, a half-open circuit breaker, upstream timeouts, correlation IDs, race-tested concurrency and a live HTTP demo. |
| 7 | [Document Intelligence Platform](https://github.com/LAKSHAY-ATREJA/Document-Intelligence-Platform) | Multi-PDF analysis for summaries, entity extraction, document comparison, and source-attributed Q&A using LangChain and FAISS. |
| 8 | [RAG Eval Kit](https://github.com/LAKSHAY-ATREJA/RAG-Eval-Kit) | Dependency-light retrieval evaluation library and CLI with standard ranking metrics, retriever comparison, automated tests, and JSON/CSV export. |
| 9 | [Fluid Dynamics Video Analysis](https://github.com/LAKSHAY-ATREJA/Fluid-Dynamics-Video-Analysis-Application) | Computer-vision desktop app combining optical flow and shape-from-shading to estimate calibrated water velocities from video. |

For **backend/API applications**, lead with 1–2 and 4–5. For **cloud/platform/SRE applications**, promote 3–5. For **applied AI/RAG**, move 6–7 up. For **computer vision**, lead with 8.

### Level B — Role-specific supporting projects

| Project | Best short description |
|---|---|
| [Flagship Feature Flags](Flagship-Feature-Flags) | Concurrency-safe Go feature-flag service with stable percentage rollouts, attribute targeting, and an immediate kill switch. |
| [LedgerFlow](LedgerFlow) | Python/FastAPI double-entry ledger reference with idempotent transfers, an inspectable journal, a runnable HTTP demo, and automated tests; in-memory educational scope. |
| [RAGGuard](RAGGuard-AI-Platform) | Offline-first FastAPI RAG gateway reference with hybrid retrieval, heuristic input checks, citation evaluation, and a deterministic local demo. |
| [SearchGrid](SearchGrid) | Python hybrid-retrieval reference combining BM25-style ranking, deterministic hash vectors, inspectable RRF evidence, and a real HTTP demo. |
| [SLOForge](SLOForge) | Python SRE reference for error budgets and paired-window burn-rate alerts, with inspectable evidence, Prometheus rules, and a real HTTP demo. |
| [SyncSpace](SyncSpace) | TypeScript/React task-board reference using WebSockets and versioned edits to reject stale writes; no authentication or persistent storage. |
| [Online Retail Analytics](https://github.com/LAKSHAY-ATREJA/online-retail-analytics) | End-to-end analysis of roughly one million transactions, covering cleaning, SQL, revenue exploration, RFM segmentation, and a Streamlit dashboard. |
| [StockSight](https://github.com/LAKSHAY-ATREJA/StockSight-LSTM-Stock-Price-Predictor) | LSTM forecasting app with a REST API and dashboard; forecasts are experimental and not investment advice. |
| [Multi-Agent Research System](https://github.com/LAKSHAY-ATREJA/multi-agent-research-system) | Streamlit research workflow that runs five specialist agents sequentially to plan, research, analyse, write, and review a report. |

### Level C — Supporting demos and foundations

| Project | Best short description |
|---|---|
| [RAG Document Q&A](https://github.com/LAKSHAY-ATREJA/Rag-pipeline-for-Document-search-) | Streamlit PDF question-answering prototype using chunking, embeddings, FAISS retrieval, and cited responses. |
| [AI Code Reviewer](https://github.com/LAKSHAY-ATREJA/ai-code-reviewer) | Groq-powered Python code-review demo for bug/security suggestions, test generation, and code explanations; generated findings need human verification. |
| [Real-Time News Sentiment Analyser](https://github.com/LAKSHAY-ATREJA/Real-Time-News-Sentiment-Analyser) | Flask dashboard that scores fetched headlines with a custom financial lexicon and provides mock data for local use without an API key. |
| [AI Chat Assistant](https://github.com/LAKSHAY-ATREJA/AI-chat-Assistant) | Streamlit/LangChain chat demo with five personas, session conversation memory, and structured error handling. |
| [CIFAR-10](https://github.com/LAKSHAY-ATREJA/CIFAR-10) | TensorFlow/Keras image-classification study comparing a custom CNN with DenseNet121 transfer learning on CIFAR-10. |
| [Titanic Survival Prediction](https://github.com/LAKSHAY-ATREJA/Titanic-Survival-Prediction) | Foundational tabular-classification project comparing Random Forest, SVM, and Logistic Regression. |

### Projects not currently linked publicly

Your CV also lists **AgeOverflow Cloud Microservices** and the **Gaussian Splatting thesis**. I did not find public repositories or portfolio folders for these in the account scan. The profile mentions the thesis, but it has no public code link yet.

## Release status


| Project | Current publication status |
| --- | --- |
| [LedgerFlow](LedgerFlow) | Complete implementation released 8 October 2026; 8 tests and real HTTP demo passed locally |
| [Flagship Feature Flags](Flagship-Feature-Flags) | Complete Go implementation released 8 October 2026; race tests, vet, build and real HTTP demo passed locally |
| [OrderMesh](OrderMesh) | Complete Java/Spring implementation released 9 October 2026; credential-free live H2 demo passed |
| [RAGGuard AI Platform](RAGGuard-AI-Platform) | Complete offline-first Python implementation released 10 October 2026; 6 tests and real HTTP demo passed locally |
| [SyncSpace](SyncSpace) | Complete TypeScript/React/WebSocket implementation released 19 October 2026; tests, production build, live demo and visual review passed locally |
| [StreamForge](StreamForge) | Complete Python event-processing reference released 20 October 2026; 5 tests, package build and real HTTP demo passed locally |
| [PlatformKit](PlatformKit) | Complete Terraform/Kubernetes/Helm reference released 21 October 2026; tests, HTTP demo, Helm checks and Terraform formatting passed locally |
| [APISentinel](APISentinel) | Complete Go resilience gateway released 22 October 2026; race tests, vet, build and live HTTP demo passed locally |
| [SearchGrid](SearchGrid) | Complete Python hybrid-retrieval reference released 23 October 2026; 10 tests, package build and real HTTP demo passed locally |
| [SLOForge](SLOForge) | Complete Python SRE reference released 24 October 2026; 14 tests, package build and real HTTP demo passed locally |

LedgerFlow is an in-memory educational reference. Its README explains the scope and provides both an automated demo and an interactive API. Docker configuration is supplied but was not executed during local validation. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37728175826) for the published implementation on Python 3.11 and 3.12.

Flagship Feature Flags is a concurrency-safe, in-memory Go reference service. Its local checks covered race detection, vet, server compilation and live HTTP behaviour for targeting, stable rollout and kill-switch decisions. It has no authentication or persistent/distributed state, and no hosted service or production-scale claim is made. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37731672897) for the published implementation.

OrderMesh demonstrates idempotent order writes and a transactional outbox. A live H2 HTTP demo passed locally using an exact-source packaged artifact. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/37917478024) with a fresh Java 17 Maven build, four tests and the end-to-end H2 demo. PostgreSQL, Redpanda and Docker execution are not claimed.

RAGGuard AI Platform is an offline-first RAG reference gateway. Six tests, Ruff checks, compilation and a real loopback HTTP demo passed locally; the demo covered health, deterministic evidence retrieval with citations and prompt-injection rejection. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/38044357761) on Python 3.11 and 3.12 with the locked environment and the same HTTP demo. Its corpus is small and in-memory, its hash-vector retrieval and guardrails are deliberately lightweight, and the optional external model-provider path was not exercised. No hosted service or cloud deployment is claimed.

SyncSpace is an in-memory collaborative task-board reference app. Type checking, two focused tests, a production build and a real two-client WebSocket demo passed locally; desktop and mobile renders were inspected. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/39236560373) with Node 22, the locked dependency graph and the same build and WebSocket demo. It has no authentication, persistence or multi-node coordination, and no hosted service or Docker execution is claimed.

StreamForge is a single-process event-time processing reference. Five tests, Ruff checks, compilation, source and wheel builds, and a real loopback HTTP demo passed locally; the demo covered health, baseline ingestion, anomaly signalling, duplicate rejection and too-late rejection. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/39407442765) on Python 3.11 and 3.12 with the locked environment, package build and the same demo. State and deduplication IDs are in memory, the anomaly rule is a small population-z-score heuristic, and Redpanda, Docker, multi-partition recovery, load testing and hosted deployment were not exercised.

PlatformKit is an infrastructure-reference project covering an AWS Terraform foundation, hardened Kubernetes and Helm deployment examples, autoscaling, health probes and Prometheus alerts. Three manifest/HTTP tests, Ruff checks, compilation, a real loopback demo, Helm lint/template and Terraform formatting passed locally. The official AWS provider archive matched HashiCorp's checksum, but this local sandbox blocks the provider's Unix-domain socket. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/39584769436), including `terraform validate` with Terraform 1.9.8 and Prometheus rule validation with `promtool`. No AWS plan/apply, container build, cluster deployment, load test, hosted service or cloud cost is claimed.


APISentinel is a standard-library Go resilience gateway for one upstream. Seven focused tests passed under the race detector, along with `go vet`, server compilation, a credential-free loopback HTTP demo and a compiled-binary HTTP check. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/39763035922) on Go 1.23 and 1.24 with format, vet, race tests, build and the same HTTP demo. The verified behaviours cover health, path/query forwarding, correlation IDs, hop-by-hop header filtering, rate limiting, circuit opening and one half-open recovery probe. State is in memory and process-local; there is no authentication, TLS termination, trusted-proxy policy, distributed coordination, persistence or load testing. Container and hosted deployment execution are not claimed.

SearchGrid is an in-memory hybrid-retrieval reference. Ten tests, Ruff checks, compilation, source and wheel builds, and a real loopback HTTP demo passed locally; the demo covered health, ranked retrieval with both signal ranks, and invalid-query rejection. [GitHub Actions passed](https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/actions/runs/39938693845) on Python 3.11 and 3.12 with locked installs, Ruff, 10 tests, package builds and the same HTTP demo. Its four-document corpus is toy data and its vectors are deterministic token hashes, not learned embeddings. PostgreSQL/pgvector files are static deployment references and were not executed; the API is not wired to that database. Docker, authentication, persistence, load testing and hosted deployment are not claimed.

SLOForge is a stateless error-budget and multi-window burn-rate reference. Fourteen tests, Ruff checks, compilation, source and wheel builds, and a real loopback HTTP demo passed locally. The demo covered health, a fast-burn page with per-window evidence and invalid-count rejection. Prometheus YAML structure and expressions were contract-tested, but `promtool`, a running Prometheus server and real metrics were not exercised. The API trusts caller-supplied aggregate windows and has no metrics ingestion, persistence, authentication, alert delivery or incident lifecycle. Docker, load testing and hosted deployment are not claimed.

All ten planned portfolio projects have now completed their individual release gates. Local verification and hosted CI evidence are recorded separately for each release.

