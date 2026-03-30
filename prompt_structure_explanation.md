# Prompt Structure Breakdown for AI Test Automation

The test automation pipeline utilizes a modular prompt system driven by a single "Skill File" (`skills/api_testing_skill.md`). This file acts as the single source of truth for all templates and static context. The Python scripts use a `SkillFile` class to load the appropriate template from this markdown file and dynamically inject variables (placeholders) at runtime.

This document breaks down the prompt structure for each phase of the pipeline, with a specific focus on **which sections of the Skill File are injected into the prompts**.

## 1. Phase 1: Scenario Generation (`scenario_generation`)
This phase turns a User Story into a strict, step-by-step JSON array of test cases.

* **Used By:** `src/generators/scenario_generator.py`
* **Prompt Template Source:** `## SECTION: Prompt — Scenario Generation`
* **Variables Injected:**
  * `{{PRODUCT_CONTEXT}}`: **Injected directly from `## SECTION: Product Context` in the skill file.**
  * `{{TEST_CASE_FORMAT}}`: **Injected directly from `## SECTION: Test Case JSON Format` in the skill file.** This is critical as it defines the strict schema (the JSON blocks, required fields like `steps` and `store_from_response`) the LLM must adhere to.
  * `{{USER_STORY}}`: The user story text from the runtime input.
  * `{{API_DOCUMENTATION}}`: The specific API docs mapped for this story.

## 2. Phase 2: Code Generation (`code_generation`)
This phase takes the human-reviewed JSON scenarios from Phase 1 and converts them into runnable `pytest` code.

* **Used By:** `src/generators/code_generator.py`
* **Prompt Template Source:** `## SECTION: Prompt — Code Generation`
* **Variables Injected:**
  * `{{PRODUCT_CONTEXT}}`: **Injected directly from `## SECTION: Product Context` in the skill file.**
  * `{{TEST_CASES_JSON}}`: The generated JSON array from Phase 1. 

*(Note: Phase 2 does NOT use the story, Swagger, or test case format sections of the skill file. It strictly relies on the output of Phase 1 and the Product Context).*

## 3. Phase 3: Self-Healing (`self_heal`)
If Pytest runs the generated code and fails, this prompt sends the broken code and the error stack trace back to the LLM to fix it.

* **Used By:** `src/generators/self_healer.py`
* **Prompt Template Source:** `## SECTION: Prompt — Self Heal`
* **Variables Injected:**
  * `{{PRODUCT_CONTEXT}}`: **Injected directly from `## SECTION: Product Context` in the skill file.**
  * `{{TEST_CODE}}`: The complete text of the failing `test_*.py` file.
  * `{{FAILURE_OUTPUT}}`: The Pytest standard terminal output/stack trace.
