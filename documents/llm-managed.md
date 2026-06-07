# NRP-Managed LLMs

Source: https://nrp.ai/documentation/userdocs/ai/llm-managed

The NRP hosts a rotating catalog of open-weights LLMs, accessible either through hosted **chat interfaces** in the browser or programmatically via an **OpenAI-compatible API**. Models are added and retired as the open-weights frontier moves.

[Chat with NRP LLMs →](https://nrp-openwebui.nrp-nautilus.io) Open WebUI in your browser — no setup required [Get an API token →](/llmtoken) Programmatic access via OpenAI-compatible endpoint ## Pick a model

Every active model is compared side-by-side in the feature matrix, and each has a card with strengths, trade-offs, and recommended uses. A few quick recommendations:

- **Frontier reasoning, longest context, multimodal** — `qwen3`
- **Agentic coding** — `kimi`, `glm-5`, or `minimax-m2`
- **Multimodal with audio** (ASR, speech-to-text) — `gemma-small`
- **Reproducible research / general-purpose LTS** — `gpt-oss`
- **Embeddings for vector search** — `qwen3-embedding`

[Available models & feature matrix](/documentation/userdocs/ai/llm-managed/models) Compare every model side-by-side; jump to any model card [Model lifecycle & changelog](/documentation/userdocs/ai/llm-managed/lifecycle) What's been added, deprecated, or removed — and why ## Use the LLMs

For browser chat, the **NRP Open WebUI** is the most full-featured option. The same OpenAI-compatible API works with desktop apps like Cherry Studio and Chatbox.

For programmatic [API access](/documentation/userdocs/ai/llm-managed/api-access), the OpenAI-compatible endpoint at `https://ellm.nrp-nautilus.io/v1` works with the OpenAI Python client, `curl`, or any compatible library. The [API access](/documentation/userdocs/ai/llm-managed/api-access) page also covers `cache_salt` — recommended for any tenant where prompts shouldn’t be cached across users.

For coding CLIs, ready-to-paste configs are provided for **Claude Code**, **OpenCode**, **Crush**, **Kimi CLI**, **pi**, and **Copilot CLI**.

[Chat interfaces](/documentation/userdocs/ai/llm-managed/chat-interfaces) Open WebUI, Cherry Studio, and Chatbox [API access](/documentation/userdocs/ai/llm-managed/api-access) Endpoint, examples, and cache_salt isolation [Client configurations](/documentation/userdocs/ai/llm-managed/client-configs) Configs for the major coding CLIs ## Operate responsibly

The NRP applies a **Fair Use Policy** with per-model concurrency limits — please review it before sending high-volume traffic. SDSC and Internet2 affiliates get higher limits. For real-time capacity and health, the **LLM Status** page surfaces live Prometheus / vLLM metrics, with one card per Kubernetes container.

[Fair use policy](/documentation/userdocs/ai/llm-managed/fair-use) Per-model concurrency limits and retry guidance [Live LLM status](/llm-status) Live deployment health from Prometheus / vLLM ## Deploy your own model

If the managed catalog doesn’t fit your need, the NRP supports running your own LLM via vLLM or SGLang. See [Managing AI Models](/documentation/admindocs/ai/managing_models/) for the deployment path.
