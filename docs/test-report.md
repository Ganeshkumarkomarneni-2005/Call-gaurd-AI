# CallGuard AI — Test Report

**Version:** 1.0  
**Status:** PASSED (100%)  
**Last Updated:** 2026-09-21  
**Test Framework:** Pytest 9.1.1 + pytest-asyncio + Starlette TestClient  

---

## Test Execution Summary

| Category | Total | Passed | Failed | Skipped | Status |
|----------|-------|--------|--------|---------|--------|
| Health API (`test_health.py`) | 2 | 2 | 0 | 0 | PASSED |
| Authentication (`test_auth.py`) | 8 | 8 | 0 | 0 | PASSED |
| Call Management (`test_calls.py`) | 8 | 8 | 0 | 0 | PASSED |
| Dashboard (`test_dashboard.py`) | 4 | 4 | 0 | 0 | PASSED |
| E2E Simulation & 9 Agents (`test_simulation.py`) | 3 | 3 | 0 | 0 | PASSED |
| **TOTAL** | **25** | **25** | **0** | **0** | **PASSED (100%)** |

---

## Test Run Details

```text
backend/tests/test_auth.py::test_register_new_user PASSED
backend/tests/test_auth.py::test_register_duplicate_email PASSED
backend/tests/test_auth.py::test_login_correct_credentials PASSED
backend/tests/test_auth.py::test_login_wrong_password PASSED
backend/tests/test_auth.py::test_login_nonexistent_user PASSED
backend/tests/test_auth.py::test_get_current_user PASSED
backend/tests/test_auth.py::test_get_current_user_no_token PASSED
backend/tests/test_auth.py::test_get_current_user_bad_token PASSED
backend/tests/test_calls.py::test_post_incoming_call PASSED
backend/tests/test_calls.py::test_post_incoming_call_missing_fields PASSED
backend/tests/test_calls.py::test_list_calls_requires_auth PASSED
backend/tests/test_calls.py::test_list_calls PASSED
backend/tests/test_calls.py::test_get_call_detail PASSED
backend/tests/test_calls.py::test_get_call_not_found PASSED
backend/tests/test_calls.py::test_end_call PASSED
backend/tests/test_calls.py::test_end_call_not_found PASSED
backend/tests/test_dashboard.py::test_dashboard_statistics_requires_auth PASSED
backend/tests/test_dashboard.py::test_dashboard_statistics PASSED
backend/tests/test_dashboard.py::test_dashboard_recent_calls PASSED
backend/tests/test_dashboard.py::test_dashboard_risk_summary PASSED
backend/tests/test_health.py::test_health_check PASSED
backend/tests/test_health.py::test_root_endpoint PASSED
backend/tests/test_simulation.py::test_simulate_ai_recruiter_call PASSED
backend/tests/test_simulation.py::test_simulate_fraud_call PASSED
backend/tests/test_simulation.py::test_simulation_reflected_in_dashboard PASSED

======================= 25 passed, 2 warnings in 4.90s ========================
```
