# Test Plan: Public Practice Targets (Restful-Booker API, SauceDemo UI)

| Field | Value |
|---|---|
| Document ID | TP-QAP-001 |
| Version | 1.0 |
| Author | Roman Szlazak |
| Status | Approved for execution |
| Related repo | `qa-automation-portfolio` |

## 1. Introduction

This plan describes how the automated suites in this repository test two public practice systems:

- **Restful-Booker** (`https://restful-booker.herokuapp.com`): a REST API for hotel bookings, published as a target for API testing practice.
- **SauceDemo** (`https://www.saucedemo.com`): a demo web shop published by Sauce Labs for UI automation practice.

Both systems are treated as if they were an internal service and front end under test. The structure of this plan follows the usual sections of an IEEE 829 / ISO 29119-3 style test plan, trimmed to what an automation project needs.

## 2. Objectives

1. Verify the main business flows work end to end (create, read, update and delete a booking; log in, add to cart, check out).
2. Verify the systems reject invalid input and unauthorized actions, and that rejected actions do not change data.
3. Verify the API keeps its response contract (JSON Schema).
4. Run a passive security baseline (headers, TLS, cookies, access control) and record findings.
5. Give fast, repeatable feedback on every push and pull request.

## 3. Scope

### 3.1 In scope

| Area | Features |
|---|---|
| API - auth | Token creation, invalid credentials, Basic auth |
| API - bookings | Create, get, list, filter, full update, partial update, delete |
| API - validation | Missing required fields, unknown IDs, business rules (dates, price) |
| API - contract | JSON Schema for booking, created booking, token and ID list |
| UI - login | Valid user, locked user, wrong password, unknown user, empty fields, logout |
| UI - shop | Add and remove items, cart badge, sorting, checkout with totals check, checkout form validation |
| Security (passive) | Security headers, TLS version and certificate, HTTP to HTTPS redirect, cookie flags, page access without login, API write access without or with a bad token, error message leakage |
| Postman | The same API flow as a Postman collection, run by Newman |

### 3.2 Out of scope

| Item | Reason |
|---|---|
| Load and performance testing | Would put load on free third-party services that did not ask for it. A response time sanity check (5 s) exists in the Postman collection only. |
| Active security testing (injection, fuzzing, brute force, active ZAP scan) | Not permitted against systems we do not own. Would be done only on an owned target or under a signed scope. |
| Cross-browser and mobile | Chromium only, to keep CI fast. Firefox and WebKit are one CLI flag away (`--browser firefox`). |
| Visual regression and accessibility | Possible next step (for example axe-core), not part of this baseline. |
| Data persistence and database checks | No database access to the targets. |
| Other SauceDemo users (`problem_user`, `performance_glitch_user`, ...) | Kept for a later iteration; they are useful for showing how tests catch UI defects. |

## 4. Test approach

### 4.1 Test levels and types

| Type | Tool | Location |
|---|---|---|
| API functional and negative | pytest + requests | `tests/api` |
| API contract | jsonschema (draft 2020-12) | `tests/api`, schemas in `src/qa_portfolio/api/schemas.py` |
| UI end to end | Playwright for Python, Page Object Model | `tests/ui`, pages in `src/qa_portfolio/pages` |
| Security, passive | pytest + requests + ssl + Playwright | `tests/security` |
| Security, baseline scan | OWASP ZAP baseline (passive), manual workflow | `.github/workflows/zap-baseline.yml` |
| API collection | Postman + Newman | `postman/` |

### 4.2 Test design techniques

- **Equivalence partitioning and boundary values**: price 0 and 1,000,000; IDs 0, -1, non-numeric and very large; month boundary and leap day dates.
- **Data-driven tests**: `pytest.mark.parametrize` for credentials, booking variants, invalid IDs, checkout form fields and sort orders.
- **State checks after negative actions**: every rejected write is followed by a read to prove the record did not change.
- **Positive control**: valid Basic auth is tested next to invalid auth, so a 403 is proven to come from authorization and not from a broken request.
- **Known defects as strict xfail**: the test states the correct behaviour; the mark states today's behaviour. If the defect is fixed, the test turns red and the mark must be removed.

### 4.3 Test data

- Each API test creates its own booking with a unique name and deletes it in fixture teardown, even on failure. Tests never depend on data created by other users of the shared API.
- UI tests use the demo accounts printed on the SauceDemo login page.
- All credentials are public demo credentials and can be overridden through environment variables (see README).

## 5. Entry and exit criteria

**Entry**

- Target responds to a health check (`GET /ping` returns 201; SauceDemo login page loads).
- Lint (ruff) passes.

**Exit**

- 100% of non-xfail tests pass in CI.
- Every xfail has a written reason prefixed `KNOWN DEFECT` or `SECURITY FINDING`.
- HTML reports are attached to the CI run.

## 6. Environments

| Environment | Detail |
|---|---|
| CI | GitHub Actions, `ubuntu-latest`, Python 3.12, Node 22, headless Chromium |
| Local | Python 3.11+, any OS supported by Playwright |
| Targets | Public, shared, reset by their owners on their own schedule |

## 7. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Free hosting is slow or sleeps (Heroku) | Timeouts, false failures | HTTP retries on 502/503/504 for idempotent methods only; pytest reruns only on network errors; every rerun visible in the report |
| Shared data changed by other users | Flaky lookups | Unique test data per test, cleanup in teardown, no assumptions about existing records |
| Target changes behaviour or markup | Failing tests | `data-test` selectors, strict xfail on known defects, failures produce screenshot, trace and report |
| A target fixes a known finding | XPASS turns CI red | Intended: update the known-findings list in the same PR |

## 8. Deliverables

- Automated suites and CI pipeline (this repository).
- Per-run artifacts: pytest-html reports for each suite, JUnit XML, Newman HTML report, Playwright traces and screenshots on failure.
- Known defects and security findings list (README).

## 9. Defect reporting

In a real project each `KNOWN DEFECT` would link to a Jira ticket in its xfail reason, for example `reason="KNOWN DEFECT BOOK-123: ..."`. Here the reason text in the test is the record.
