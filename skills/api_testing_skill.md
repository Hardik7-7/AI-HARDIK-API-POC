# API Testing Skill

This file is the **single source of truth** for all LLM prompts used in the AI Backend Test Automation pipeline.
It defines product-specific context, the test case JSON format, and prompt templates for each phase.

> **How to use:** Edit the sections below to match your product. The prompt templates use `{{PLACEHOLDER}}` syntax — 
> these are automatically filled at runtime by `prompt_builder.py`. Do NOT change placeholder names.

---

## SECTION: Product Context

<!-- 
  Edit this section to describe the product you are testing.
  The LLM will use this context to write more accurate, domain-aware test cases.
  Include: what the product does, auth model, known quirks, base URL pattern, error conventions.
-->

### Product Overview

What EigenServ is 
EigenServ is a KVM-based virtual infrastructure management platform 
with cloud-ready capabilities, including Google Cloud Platform support 
and API-driven compliance management. It is designed to help 
organizations manage virtual machines and infrastructure consistently across 
on-premise and cloud environments, offering automation, monitoring, and 
governance features through a centralized system. 

## Authentication
- **Type:** Token
- **Header:** `Authorization: Token <token>`
- **Token source:** Obtained via `POST /auth/` with JSON `{"username": "...", "password": "..."}`; response contains `token`

## Base URL Pattern
- **Test-Server:** `http://<test-host>:8086`

```

---

## SECTION: Test Case JSON Format

This defines the exact JSON structure the LLM must produce during Phase 1 (Scenario Generation).
Each element in the array represents one test case. Steps within a test case can reference outputs from previous steps.

```json
[
  {
    "id": "TC-001",
    "base_url": "http://192.168.1.10:8086",
    "title": "Short descriptive title of the test",
    "description": "Full description of what this test validates",
    "tags": ["smoke", "create", "happy-path"],
    "priority": "high",
    "preconditions": [
      "User is authenticated",
      "Resource with ID 'test-resource-1' exists"
    ],
    "steps": [
      {
        "step": 1,
        "action": "Human-readable description of this step",
        "request": {
          "method": "POST",
          "endpoint": "/api/v1/resource",
          "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer {{AUTH_TOKEN}}"
          },
          "body": {
            "name": "TestItem",
            "type": "standard"
          }
        },
        "expected": {
          "status_code": 201,
          "body_contains": {
            "id": "__non_empty__",
            "name": "TestItem",
            "status": "ACTIVE"
          },
          "store_from_response": {
            "resource_id": "$.id"
          }
        }
      },
      {
        "step": 2,
        "action": "Verify the created resource can be fetched",
        "request": {
          "method": "GET",
          "endpoint": "/api/v1/resource/{{resource_id}}",
          "headers": {
            "Authorization": "Bearer {{AUTH_TOKEN}}"
          }
        },
        "expected": {
          "status_code": 200,
          "body_contains": {
            "id": "{{resource_id}}",
            "name": "TestItem"
          }
        }
      }
    ],
    "teardown": [
      {
        "action": "Delete the created resource",
        "request": {
          "method": "DELETE",
          "endpoint": "/api/v1/resource/{{resource_id}}"
        }
      }
    ]
  }
]
```

### Field Reference

| Field | Required | Description |
|---|---|---|
| `id` | ✅ | Unique identifier, e.g. `TC-001` |
| `base_url` | ❌ | Full base URL if provided/derived from story (e.g. `http://...:8086`) |
| `title` | ✅ | Short descriptive title |
| `description` | ✅ | What this test validates |
| `tags` | ✅ | List of tags: `smoke`, `regression`, `happy-path`, `edge-case`, `auth`, `crud` |
| `priority` | ✅ | `high`, `medium`, or `low` |
| `preconditions` | ❌ | List of conditions that must be true before the test runs |
| `steps` | ✅ | Ordered list of HTTP request/response steps |
| `steps[].step` | ✅ | Step number (1-indexed) |
| `steps[].action` | ✅ | Human-readable description of this step |
| `steps[].request` | ✅ | HTTP request definition |
| `steps[].expected` | ✅ | Expected response definition |
| `steps[].expected.store_from_response` | ❌ | JSONPath expressions to capture values for later steps |
| `teardown` | ❌ | Cleanup steps to run after the test (regardless of pass/fail) |

### Placeholder Conventions
- `{{AUTH_TOKEN}}` — filled at runtime with a valid bearer token
- `{{resource_id}}` — filled with a value captured in a previous step via `store_from_response`
- `__non_empty__` — asserts the field exists and is not null/empty

---

## SECTION: Prompt — Scenario Generation

<!--
  PROMPT TEMPLATE: scenario_generation
  Used by: src/generators/scenario_generator.py
  Purpose: Generate a structured list of test cases in JSON format.
-->

### PROMPT_START: scenario_generation

You are a senior QA engineer and API testing expert. Your job is to generate a comprehensive set of API test cases in a structured JSON format.

---

**PRODUCT CONTEXT:**
{{PRODUCT_CONTEXT}}

---

**USER STORY:**
{{USER_STORY}}

---

**API DOCUMENTATION (Use this as your strict schema reference):**
{{API_DOCUMENTATION}}

---

**TEST CASE FORMAT TO USE:**
{{TEST_CASE_FORMAT}}

---

**YOUR TASK:**
Generate a thorough list of test cases for the user story and APIs provided above. Include:
- Happy path tests (valid inputs, expected success)
- Negative tests (invalid inputs, missing fields, wrong types)
- Edge cases (boundary values, empty lists, max lengths)
- Authorization tests (missing token, invalid token, insufficient permissions)
- Dependency chain tests (create → read → update → delete flows as multi-step test cases)

Rules:
- STRICT COMPLIANCE: You MUST strictly adhere to the provided API documentation. Do not invent fields. Respect all required fields, data types, and allowed enum values.
- URL HANDLING: Keep all 'endpoint' paths STRICTLY relative (e.g., `/api/v1/resource`). If the User Story provides a test host (e.g., an IP or domain), calculate the full Base URL by replacing `<test-host>` in the Base URL Pattern with that host but KEEP the port (e.g., `http://192.168.1.10:8086`). Place this derived URL in the top-level `base_url` field of the test case JSON.
- AUTHENTICATION: Ensure every request step includes the correct authentication headers as defined in the Product Context.
- REALISTIC DATA: Do not use generic strings like 'TestItem' or 'test_user'. Ensure all resource names, descriptions, and payload values are highly realistic and strictly relevant to the User Story context.
- ASSERTIONS: When filling `expected.body_contains`, ONLY assert on stable unique identifiers (e.g. `id`, `uuid`) or deterministic fields like `status`. DO NOT assert on mutable strings like `name`, `description`, or specific error messages, as these are subject to change and cause tests to erroneously fail.
- Return ONLY a valid JSON array. No explanation text, and absolutely NO markdown formatting or ```json block — raw JSON only.
- Each test case must have: `id`, `title`, `description`, `tags`, `priority`, `steps`.
- Steps must include complete `request` and `expected` objects.
- Use `store_from_response` for values that flow between steps.
- IDs must be sequential: TC-001, TC-002, etc.

### PROMPT_END: scenario_generation

---

## SECTION: Prompt — Code Generation

<!--
  PROMPT TEMPLATE: code_generation
  Used by: src/generators/code_generator.py
  Purpose: Convert reviewed JSON test cases into runnable pytest code.
-->

### PROMPT_START: code_generation

You are a senior Python test automation engineer. Your job is to convert structured JSON test cases into clean, runnable `pytest` code.

---

**PRODUCT CONTEXT:**
{{PRODUCT_CONTEXT}}

---

**TEST CASES (reviewed and approved JSON):**
{{TEST_CASES_JSON}}

---

**YOUR TASK:**
Generate a complete, runnable Python pytest test file.

### Test File Requirements:
1. Only import standard library modules or third-party packages that you explicitly use. Only use `requests` library for HTTP calls.
2. Each JSON test case becomes exactly one `test_` function.
3. Function name derived from `id` and `title`: `def test_TC001_create_resource():`
4. Each function must have a single docstring matching the test case `description`.
5. Implement the multi-step flow: execute steps in order, store values from `store_from_response`, pass them to subsequent steps.
6. To store values from the response using JSONPath expressions (as defined in `store_from_response`), implement extraction logic in your test using `jsonpath_ng` or simple python dictionary parsing.
7. **TEARDOWN / CLEANUP RULES (CRITICAL):**
   - Use `try/finally` around all test steps so teardown always runs.
   - Wrap cleanup calls (DELETE/teardown) in `try/except Exception: pass` so cleanup failures emit a warning and do NOT re-raise (cleanup issues must never fail the test).
   - Never put bare `assert` statements in a `finally` block.
8. Add clear assertion messages so failures are easy to debug.
9. Keep all test functions in one file.
10. **ASSERTION RULES**: ONLY assert on HTTP status codes. DO NOT assert on specific string error messages in the response body, as these are subject to change and can cause brittle tests.

### Coding Style Rules (strictly enforced):
- **NO hallucinated imports.** Only import standard library or third-party packages you actually use.
- **NO unnecessary comments.** The ONLY allowed comments are:
  - The module-level docstring (if any).
  - The per-function docstring.
  - Short inline comments on a single line that explain a non-obvious step (e.g., `# step 2: fetch the created resource`).
  - Do NOT add section-divider comments, TODO comments, "Note:" blocks, or any commentary that restates what the code already clearly shows.

### Output Format:
Output ONLY the raw Python test file. No markdown fences (` ```python ``` `). No section headers. No explanation text before or after the code.

### PROMPT_END: code_generation

---

## SECTION: Prompt — Self Heal

<!--
  PROMPT TEMPLATE: self_heal
  Used by: src/generators/self_healer.py
  Purpose: Given failing test code and error output, generate a fixed version.
-->

### PROMPT_START: self_heal

You are a senior Python test automation engineer. A pytest test file has been run and some tests are failing. Your job is to fix the failing tests.

---

**PRODUCT CONTEXT:**
{{PRODUCT_CONTEXT}}

---

**ORIGINAL TEST FILE:**
```python
{{TEST_CODE}}
```

---

**PYTEST FAILURE OUTPUT:**
```
{{FAILURE_OUTPUT}}
```

---

**YOUR TASK:**
Analyze the failure output and fix the test code. Common issues to look for:
- Wrong status code assertions (check if API actually returns a different code)
- Wrong field names in body assertions (typos, case differences)
- Missing headers or wrong header values
- Incorrect URL paths or path parameters
- Serialization issues (e.g., sending int where string expected)
- Missing setup steps (endpoint requires prior resource to exist)
- Incorrect JSONPath expressions in `store_from_response`
- **Incorrect imports:** Remove any import line that tries to import a non-existent module.

**TEARDOWN / CLEANUP RULES (CRITICAL — read carefully):**
- Cleanup code (DELETE calls, teardown steps, finally blocks) **MUST NOT** cause a test FAILURE.
- Wrap cleanup in `try/except Exception: pass` (never re-raise) to prevent test failure on cleanup errors.
- Never put bare `assert` statements inside teardown / finally blocks.

### Coding Style Rules (strictly enforced):
- **NO hallucinated imports.** Only keep imports for standard library or third-party packages you actually use.
- **NO unnecessary comments.** The ONLY allowed comments are:
  - The module-level docstring (if any).
  - The per-function docstring.
  - Short inline comments on a single non-obvious step.
  - Do NOT add section-divider comments, TODO comments, "Note:" blocks, or any commentary that restates what the code clearly shows.

### Rules:
- Return ONLY the complete fixed Python file.
- Do NOT remove any test functions. Fix them, don't delete them.
- If a test cannot be fixed without more information, add a `pytest.skip()` with a clear reason.
- Keep all imports and structure intact (except removing unused imports).
- ABSOLUTELY NO markdown code fences anywhere in your output.
- No explanation text before or after the code.

### PROMPT_END: self_heal
