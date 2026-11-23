# LLMs, Agents, RAG & MCP Cheatsheet

## 1. LLM fundamentals
- **Transformer (decoder-only)**: token embeddings → N × [self-attention + MLP, with residuals + LayerNorm] → next-token logits
- **Attention**: Attn(Q,K,V) = softmax(QKᵀ/√dₖ + mask)·V. The √dₖ keeps the logits' variance ~1 so softmax doesn't saturate
  - Multi-head: attend in h subspaces in parallel. GQA/MQA share K/V across heads → smaller KV cache
  - Cost O(n²·d) in sequence length n → long context is expensive; mitigations: FlashAttention (IO-aware, exact), sliding window, sparse attention
- **Positional info**: RoPE (rotates Q/K by position; extrapolates with scaling), ALiBi
- **Tokens**: subword BPE. ~4 chars ≈ 1 token in English; numbers tokenise badly → arithmetic is unreliable, so use a tool
- **Training pipeline**: pretraining (next-token prediction on huge corpora) → SFT (instruction data) → preference tuning (RLHF with a reward model + PPO, or DPO directly on preference pairs; RLAIF / constitutional) → RL on verifiable rewards (maths, code) for reasoning models
- **Scaling laws**: loss falls as a power law in params, data and compute. Chinchilla: ~20 tokens per parameter is compute-optimal
- **MoE**: router sends each token to the top-k of E experts → many params, few active per token
- **Inference**:
  - *Prefill* (process the prompt, compute-bound, parallel) vs *decode* (one token at a time, memory-bandwidth-bound)
  - **KV cache** memory ≈ 2 × layers × kv_heads × d_head × seq_len × bytes. It is the bottleneck for long context / large batches
  - Speedups: batching (continuous batching), quantisation (INT8/INT4, FP8), speculative decoding (a small draft model + verification), prefix/prompt caching
- **Decoding**: greedy, temperature (T→0 = argmax), top-k, top-p (nucleus). Output is non-deterministic even at T=0 (batching, floating point)
- **Fine-tuning**: full fine-tune vs PEFT — **LoRA** (W + BA with low rank r; trains ~0.1–1% of params), QLoRA (LoRA on a 4-bit base)
- **Failure modes**: hallucination, sycophancy, knowledge cutoff, sensitivity to prompt wording, lost-in-the-middle (weaker recall mid-context), weak exact arithmetic

## 2. Prompting & using models well
- Clear task + context + output format in the system prompt; examples (few-shot) for format/style
- **Reasoning**: chain-of-thought ("think step by step") or models with built-in thinking; trade latency/cost for accuracy
- **Structured output**: JSON schema / constrained decoding → reliable parsing
- **Prompt caching**: caching is a *prefix* match → put stable content (instructions, tools, documents) first and volatile content last
- **Evals before tuning**: fixed test set + grader (exact match, code-based checks, LLM-as-judge with a rubric). Measure, change one thing, re-measure
- Cost ∝ input + output tokens; output tokens cost more and dominate latency

## 3. RAG (Retrieval-Augmented Generation)
**Why**: ground answers in private / fresh data, cite sources, reduce hallucination — without retraining.

**Pipeline**
```
Ingest:  documents → parse → chunk → embed → vector index (+ keyword index)
Query:   question → (rewrite) → retrieve top-k → rerank → put into prompt → generate with citations
```
| Stage | Key choices |
|---|---|
| Chunking | fixed-size with overlap, or by structure (headings, sections, tables); ~200–1000 tokens; add title/section metadata. *Contextual retrieval*: prepend a short chunk summary before embedding |
| Embeddings | bi-encoder → dense vectors; similarity = cosine (= dot product on normalised vectors) |
| Index / ANN | HNSW (graph, fast, memory-heavy), IVF (cluster then search), PQ (compressed); trade recall vs latency |
| Hybrid search | BM25 (exact terms: tickers, CUSIPs, numbers) + dense (semantics); fuse with **RRF**: score = Σ 1/(k + rankᵢ), k≈60 |
| Reranking | cross-encoder scores (query, chunk) pairs jointly; more accurate, so run it only on the top ~50 |
| Query side | query rewriting, multi-query, HyDE (embed a hypothetical answer), metadata filters (date, issuer) |
| Generation | "answer only from context; say if unknown"; cite chunk IDs |

**Evaluation**
- Retrieval: recall@k, precision@k, MRR, nDCG
- Generation: faithfulness/groundedness (are claims supported by the context?), answer relevance, citation accuracy
- Build a labelled set of question → relevant docs → reference answer

**Failure modes**: wrong chunking (tables split), the relevant chunk missing from top-k, stale index, conflicting docs, the model ignoring context, prompt injection hidden in documents.

**RAG vs fine-tuning vs long context**
| | Use when |
|---|---|
| RAG | knowledge is large, changing, or needs citations / access control |
| Long context | corpus fits in the window and per-query cost/latency is acceptable; simplest option |
| Fine-tuning | changing *behaviour*/format/style or a narrow skill, not adding facts |

## 4. Agents
**Definition**: an LLM in a loop that chooses actions (tool calls), observes results and continues until done.
```
while not done:
    response = model(history, tools)
    if response has tool_calls: run them → append results to history
    else: done
```
- **Workflow vs agent**: workflow = code decides the steps (predictable, cheaper); agent = model decides (flexible, for open-ended tasks). Start with the simplest thing that works
- **Common patterns** (from Anthropic's "Building effective agents"):
  - *Prompt chaining*: fixed sequence of LLM calls, with checks between
  - *Routing*: classify the input → specialised prompt/model
  - *Parallelisation*: sectioning (split the work) or voting (run several times, aggregate)
  - *Orchestrator–workers*: a lead model splits the task dynamically and delegates to sub-agents
  - *Evaluator–optimiser*: generate → critique → revise loop
- **ReAct**: interleave reasoning and acting (thought → action → observation)
- **Tool design** matters most: clear names and descriptions, typed schemas, informative errors, idempotent where possible, return concise results (context is a budget)
- **Memory**: short-term = the context window; long-term = files / DB / vector store the agent reads and writes; context management = summarise/compact or clear old tool results
- **Multi-agent**: parallel sub-agents with fresh contexts for breadth (research); costs many more tokens; hard to coordinate shared state
- **Reliability**: max steps / budgets, verification steps (tests, schema checks), human approval for irreversible actions, logging/tracing every step
- **Security**:
  - **Prompt injection** (untrusted text in tool results gives instructions)
  - Data exfiltration
  - Over-privileged tools
  - Mitigations: least privilege, sandboxing, treat tool output as data, allow-lists, confirmation gates
- **Agent evals**: task success rate on realistic tasks, steps/tokens/cost per task, pass@k vs pass^k (consistency), trajectory review

## 5. MCP (Model Context Protocol)
**What**: an open protocol (introduced by Anthropic in 2024) that standardises how AI applications connect to tools and data. It turns M apps × N integrations into M + N ("USB-C for AI").

**Architecture**
```
Host (AI app, e.g. IDE / chat app) ── contains ── MCP Client(s) ──1:1── MCP Server (wraps a DB, API, files…)
```
- Wire format: **JSON-RPC 2.0**
- **Transports**: `stdio` (local subprocess) and **Streamable HTTP** (remote; superseded the older HTTP+SSE transport)
- **Lifecycle**: `initialize` (exchange protocol version + capabilities) → normal operation → shutdown
- **Auth** for remote servers: OAuth 2.1

**Primitives**
| Side | Primitive | Controlled by | Purpose |
|---|---|---|---|
| Server | **Tools** | model | actions with JSON-schema inputs (`tools/list`, `tools/call`) |
| Server | **Resources** | application | read-only context addressed by URI (files, DB rows) |
| Server | **Prompts** | user | reusable templates / slash commands |
| Client | **Sampling** | server asks the host's LLM to generate | server-side agentic behaviour without its own model |
| Client | **Roots** | client | filesystem/URI boundaries the server may operate in |
| Client | **Elicitation** | server asks the user for input | structured follow-up questions |

- **MCP vs plain function calling**: function calling is the model ↔ app interface; MCP is the app ↔ tool-provider interface (discovery, transport, auth), so tools become reusable across hosts
- **Security**: tool poisoning (malicious tool descriptions), prompt injection via results, confused-deputy / token passthrough, over-broad scopes → vet servers, least privilege, human confirmation for writes

## 6. Quant / finance angle
- **Use cases**: sentiment and event extraction from news / filings / earnings calls → features; RAG over research notes, term sheets, ISDA docs; agents for data cleaning, report generation, code assistants for research; trader/sales copilots; summarising RFQ / chat flow
- **LLM features as alpha**: treat them like any other signal — IC, decay, turnover, out-of-sample tests, transaction costs
- **Look-ahead bias**: the model's pretraining data includes the "future" relative to the backtest date → leakage. Use models with a knowledge cutoff before the test period, or point-in-time data only
- **Not for the low-latency path**: inference takes 100 ms to seconds, so use LLMs offline/batch or for slow signals, never inside the market-making quote loop
- **Numbers**: never trust LLM arithmetic or extracted figures without validation; compute with code tools; cross-check against source data
- **Determinism & audit**: log prompts, model version and outputs; pin model versions; reproducibility for model risk management
- **Compliance**: MNPI / client data handling, data residency, vendor risk, model governance (SR 11-7-style validation)

## 7. Classic interview questions
1. Why divide by √dₖ in attention? → Keeps the dot products' variance ~1; otherwise softmax saturates and gradients vanish.
2. What dominates inference latency for long outputs? → Decode: memory-bandwidth-bound and sequential. KV cache size limits the batch.
3. RAG returns irrelevant chunks — how do you debug? → Measure retrieval separately (recall@k on a labelled set); fix chunking, add hybrid BM25, a reranker, metadata filters, query rewriting.
4. RAG vs fine-tuning for internal research Q&A? → RAG (fresh data, citations, permissions); fine-tune only for format/behaviour.
5. How is MCP different from function calling? → MCP standardises tool discovery/transport/auth between app and tool server; function calling is how the model emits a call.
6. How do you evaluate an agent? → Task-level success on realistic cases, cost and steps per task, consistency over repeated runs, failure taxonomy from traces.
7. What is prompt injection and how do you mitigate it? → Untrusted content issuing instructions; least privilege, isolate untrusted data, confirmations, output filtering.
8. Using an LLM sentiment score in a 2015–2020 backtest — the pitfall? → The model was trained on later data → look-ahead leakage; use point-in-time or pre-cutoff models.
9. LoRA in one line? → Freeze W; learn ΔW = BA with low rank r ≪ d; few trainable params, mergeable at inference.
10. Agent or workflow for daily risk-report generation? → Workflow: fixed steps, deterministic, auditable; agent only for the open-ended commentary or investigation.
