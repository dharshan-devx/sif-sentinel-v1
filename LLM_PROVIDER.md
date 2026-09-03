# LLM Provider Architecture

## Overview

Phase J introduced an optional, provider-agnostic LLM abstraction layer to the SIF Sentinel system. The LLM acts solely as a natural language assistant for reviewers and has zero decision-making authority over safety protocols.

## Core Principles

1. **Determinism First:** All safety decisions (SIF potential, risk scoring, precursor intelligence) are driven by the deterministic pipeline and risk engine. The LLM only receives structured data to format.
2. **Fail-Safe Degradation:** If the LLM provider fails, times out, or is disabled, the system gracefully degrades. The core safety analysis continues uninterrupted.
3. **Prompt Injection Mitigation:** Report text is treated as untrusted input. The LLM context clearly delineates untrusted data from the authoritative safety results, preventing prompt injection attacks from overriding deterministic findings.
4. **Zero State:** The LLM does not store state. All provenance and metadata are persisted securely alongside the original `ReportAnalysis` record.

## Configuration

The LLM abstraction is configured via environment variables defined in `app/core/config.py`:

```bash
LLM_ENABLED=True
LLM_PROVIDER="gemini"
LLM_MODEL="gemini-2.5-flash"
LLM_API_KEY="..."
LLM_TEMPERATURE=0.0
LLM_MAX_OUTPUT_TOKENS=1024
LLM_TIMEOUT_SECONDS=10.0
```

## Adding a New Provider

The abstraction layer is designed to support multiple providers (e.g., Anthropic, OpenAI). To add a new provider:

1. Create a new file in `app/services/llm/` (e.g., `openai_provider.py`).
2. Implement the `LLMProvider` protocol (defined in `app/services/llm/provider_interface.py`).
3. Update `LLMManager.get_provider()` in `app/services/llm/manager.py` to route to your new provider when configured.

## Current Implementation

The only supported provider currently is `GeminiProvider` using the official `google-genai` SDK. It exposes the `generate_reviewer_summary` operation to summarize incident data for a human reviewer.
