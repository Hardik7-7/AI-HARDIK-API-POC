# AI Backend Test Automation POC

An LLM-powered Python pipeline that reads a **Swagger/OpenAPI spec** and a **User Story**, 
generates structured JSON test cases for human review, converts them to runnable `pytest` code, 
and self-heals test failures — all in **three separate, reviewable commands**.

---

## 🏗 Project Structure

```
AI-BACKEND-POC/
├── skills/
│   └── api_testing_skill.md       ← ✏️ Edit this: product context + prompt templates
├── inputs/
│   ├── swagger/                   ← Drop your Swagger/OpenAPI specs here
│   └── stories/                   ← Drop your user story files here
├── src/
│   ├── parsers/                   ← swagger_parser, story_parser
│   ├── llm/                       ← client (OpenAI-compatible), prompt_builder
│   ├── generators/                ← api_mapper, scenario_generator, code_generator, self_healer
│   └── utils/                     ← file_io, validators
├── output/
│   ├── mapped_apis.json           ← Intermediate: relevant endpoints identified by LLM
│   ├── test_cases.json            ← ✏️ Review & edit this after Phase 1
│   ├── tests/                     ← Generated pytest files (Phase 2 output)
│   └── reports/                   ← HTML test reports (Phase 3 output)
├── generate_scenarios.py          ← Phase 1 CLI
├── generate_tests.py              ← Phase 2 CLI
└── run_and_heal.py                ← Phase 3 CLI
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
copy .env.example .env
# Edit .env with your API key and LLM settings
```

Key env vars:
| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your LLM provider API key |
| `OPENAI_BASE_URL` | OpenAI default | Override for Azure, Ollama, etc. |
| `LLM_MODEL` | `gpt-4o` | Model to use |
| `LLM_TEMPERATURE` | `0.2` | Response creativity (lower = more deterministic) |
| `SELF_HEAL_MAX_ATTEMPTS` | `3` | Max auto-fix attempts in Phase 3 |
| `BASE_URL` | `http://localhost:8000` | Your API's base URL (used in generated tests) |
| `AUTH_TOKEN` | *(empty)* | Bearer token for authenticated tests |

---

## 🚀 Usage (3-Phase Workflow)

### Phase 1 — Generate Test Scenarios
```bash
python generate_scenarios.py \
  --swagger inputs/swagger/my_api.json \
  --story inputs/stories/my_story.md
```
Or with a live Swagger URL:
```bash
python generate_scenarios.py \
  --swagger https://api.example.com/swagger.json \
  --story inputs/stories/my_story.md
```

**What happens:**
1. LLM reads the Swagger + User Story and identifies the relevant endpoints
2. LLM generates structured test cases in JSON format
3. Output saved to `output/test_cases.json`

**➡️ Now open `output/test_cases.json` and review/edit the test cases.**

---

### Phase 2 — Generate Test Code
```bash
python generate_tests.py
```
Or with custom paths:
```bash
python generate_tests.py \
  --test-cases output/test_cases.json \
  --output-dir output/tests
```

**What happens:**
1. Reads your reviewed `test_cases.json`
2. LLM generates a complete `pytest` file
3. Output saved to `output/tests/test_generated.py`

**➡️ Review `output/tests/test_generated.py` before running.**

---

### Phase 3 — Run Tests with Self-Healing
```bash
python run_and_heal.py
```
Or with options:
```bash
python run_and_heal.py --max-attempts 5
python run_and_heal.py --no-heal   # just run, no auto-fix
```

**What happens:**
1. Runs `pytest` on the generated test file
2. If tests fail, LLM analyzes the failure output and rewrites the test code
3. Each attempt is backed up (`test_generated.attempt_1.py`, etc.)
4. Re-runs until all tests pass or max attempts reached
5. HTML reports saved to `output/reports/`

---

## 🛠 Customizing the Skill File

Edit `skills/api_testing_skill.md` to:

- **Product Context** — Describe your API's domain, auth model, error formats, known quirks
- **Prompt Templates** — Tune the 4 prompts (API mapping, scenario gen, code gen, self-heal)
- **Test Case Format** — Adjust the JSON schema reference the LLM follows

The prompt templates use `{{PLACEHOLDER}}` syntax. Available placeholders:

| Placeholder | Injected by | Description |
|---|---|---|
| `{{PRODUCT_CONTEXT}}` | Auto | Product context section from skill file |
| `{{TEST_CASE_FORMAT}}` | Auto | Test case JSON format section from skill file |
| `{{SWAGGER_CONTENT}}` | Phase 1 | Full text of the Swagger spec |
| `{{USER_STORY}}` | Phase 1 | User story text |
| `{{MAPPED_APIS}}` | Phase 1 | Relevant endpoints identified in API mapping |
| `{{TEST_CASES_JSON}}` | Phase 2 | Reviewed test cases JSON |
| `{{TEST_CODE}}` | Phase 3 | Current failing test file content |
| `{{FAILURE_OUTPUT}}` | Phase 3 | Pytest failure output |

---

## 📋 Test Case JSON Format

See `skills/api_testing_skill.md` → "Test Case JSON Format" section for the full schema reference.

Quick example:
```json
[
  {
    "id": "TC-001",
    "title": "Create item successfully",
    "description": "Verify POST /items returns 201 with valid body",
    "tags": ["smoke", "create"],
    "priority": "high",
    "steps": [
      {
        "step": 1,
        "action": "Send POST /api/v1/items",
        "request": {
          "method": "POST",
          "endpoint": "/api/v1/items",
          "body": { "name": "TestItem" }
        },
        "expected": {
          "status_code": 201,
          "body_contains": { "id": "__non_empty__" },
          "store_from_response": { "item_id": "$.id" }
        }
      }
    ]
  }
]
```

---

## 🧩 Supported LLM Providers

Any **OpenAI-compatible** API works. Set `OPENAI_BASE_URL` accordingly:

| Provider | Base URL |
|---|---|
| OpenAI | *(default, no override needed)* |
| Azure OpenAI | `https://<resource>.openai.azure.com/` |
| Ollama (local) | `http://localhost:11434/v1` |
| LM Studio | `http://localhost:1234/v1` |
