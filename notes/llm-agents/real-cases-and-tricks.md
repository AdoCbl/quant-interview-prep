# LLMs & Agents in Practice: Real Cases, Tricks and Notes

This file is the companion to [README.md](README.md), which covers the concepts. This one is about what happens when you actually build these systems.
- Part 1 lists public, real-world examples worth knowing for interviews.
- Part 2 walks through six worked designs for a trading or bank setting, each with the details interviewers probe.
- Part 3 collects practical tricks.
- Part 4 shows how to talk about this in an interview.

---

## Part 1 — Public cases worth knowing

| Case | What happened | Lesson to quote |
|---|---|---|
| **BloombergGPT** (2023) | Bloomberg trained its own 50-billion-parameter model on a mix of financial and general text. It did well on finance tasks, but general-purpose models released soon afterwards matched or beat it on many of them. | Training your own model from scratch is rarely worth it. A strong general model plus your own data (through search or fine-tuning) usually wins. |
| **Morgan Stanley Wealth Management assistant** (2023) | Morgan Stanley gave financial advisers an assistant, built on OpenAI's GPT-4, that answers questions from the firm's own library of research and procedure documents. It was one of the first large bank deployments. | A classic retrieval-augmented setup: grounded in approved internal documents, with heavy testing before launch. A good talking point for the Morgan Stanley interview. |
| **JPMorgan "LLM Suite"** (2024) | JPMorgan rolled out an internal assistant to a large share of its employees for writing, summarising and analysis. | Banks give staff internal tools rather than public chatbots, to keep data inside the firm. |
| **Samsung code leak** (2023) | Engineers pasted confidential source code into a public chatbot. Samsung then restricted use of such tools. | Data leaves the firm the moment it goes into an outside service. This is why banks use approved internal deployments. |
| **Lawyer citing invented cases** (*Mata v. Avianca*, US, 2023) | A lawyer filed a brief containing court cases that a chatbot had made up, and was sanctioned. | Never pass along model output you haven't checked. Treat citations and numbers as claims to verify. |
| **Air Canada chatbot** (2024) | The airline's website chatbot gave a customer a wrong refund policy. A tribunal held the airline responsible for what its bot said. | The firm owns whatever its model tells customers. Customer-facing answers need grounding and limits. |
| **"Can ChatGPT forecast stock prices?"** (Lopez-Lira & Tang, 2023 research paper) | They asked a model whether each news headline was good or bad for the stock. The scores predicted next-day returns. | LLMs can produce useful text signals, but such results need checks for look-ahead bias and trading costs (see case A). |
| **Look-ahead bias studies** (e.g. Glasserman & Lin, 2023) | Researchers tested whether models' "knowledge of the future" inflates backtests. One test removed company names so the model couldn't recall what happened next. | Hide identifying details, or use models trained only on data from before the test period. Expect interviewers to ask about this. |

---

## Part 2 — Worked designs

### Case A: Sentiment signal from earnings call transcripts
**Goal**: for each earnings call, produce a score from −1 to +1 for how positive management sounded about future business, and test whether it predicts the next month's returns.

**Design**
1. **Data**: use transcripts with an exact publish timestamp. The signal can only be used *after* that time. Using it earlier is a silent backtest error.
2. **Prompt**: ask for a fixed JSON output, not free text:
   ```json
   {"guidance_tone": -1.0 to 1.0, "guidance_changed": "raised|lowered|unchanged|none",
    "key_quotes": ["…"], "confidence": 0.0 to 1.0}
   ```
   Requiring `key_quotes` forces the model to point at evidence. Spot-check that each quote really appears in the transcript.
3. **Long documents**: a transcript is about 10,000–20,000 tokens, which fits in one prompt. Score the question-and-answer section separately from the prepared remarks: unscripted answers often carry more information.
4. **Batch processing**: thousands of transcripts are not urgent. Use the provider's batch service, which is usually much cheaper than live requests, and save every raw response.
5. **Fix the model version**: name the exact model version and keep the prompt in version control. If the model changes, the whole history of scores changes.

**Tricks and checks**
- **Look-ahead test**: replace the company name, ticker, people's names and dates with placeholders ("Company A", "Quarter X"). Re-run on a sample. If the scores change a lot, the model was using memory of what happened, not the text.
- **Training cutoff**: only trust backtest results for periods *after* the model's training data ends. Results from before then are suspect.
- **Calibration**: models cluster scores at round numbers (0.7, 0.8). Convert scores to ranks within each date before using them.
- **Repeatability**: run a sample twice. If the scores move a lot, ask for a categorical label (positive, neutral or negative) instead of a fine-grained number, or average several runs.
- **Compare with a cheap baseline**: test against a simple word-list sentiment score. If the LLM barely beats it, the extra cost isn't justified.
- **Signal tests, as for any signal**: correlation with future returns, how fast that fades, how often the positions turn over, and results after trading costs.

**Interview follow-ups**: "How would you know it isn't just memorised?" (the placeholder test and the post-cutoff test). "What does it cost?" (tokens per transcript × number of transcripts × price, with batch pricing).

---

### Case B: Question answering over internal research and term sheets
**Goal**: traders and salespeople ask "What's the call schedule on this callable bond?" or "What did our strategists say about the 2s10s curve last month?". The system answers with citations. (2s10s is the gap between the 2-year and 10-year yields.)

**Design details that matter**
- **Reading PDFs**: term sheets and research are full of tables. Plain text extraction scrambles them. Use a parser that keeps table structure, or send page images to a model that can read images. Test on your 20 ugliest documents first.
- **Chunking**: split by section heading. Keep each table whole as one chunk, with its caption and the section title attached. Store the document date, author, desk, product and access group as fields on each chunk.
- **Search**: combine keyword search with meaning-based (vector) search. Exact identifiers (bond codes, tickers, deal names) only match reliably with keyword search.
- **Date matters**: "last month" needs a date filter. Ask the model to turn the question into a search query *plus* filters (dates, product, desk) before searching.
- **Permissions**: filter by the user's access rights *during the search*, not after the answer is written. Otherwise restricted text can leak into the answer.
- **Citations you can check**: number each passage in the prompt and require "[3]"-style citations. Then check in code that every cited number exists, and flag answers with no citations.
- **"I don't know"**: tell the model explicitly that "not found in the documents" is an acceptable answer. Test it with questions that have no answer in the documents.

**Evaluation set**: about 100 real questions collected from users, each labelled with the correct document and answer. Score the search step (was the right document in the top 5?) separately from the answer step (was the answer correct and supported?). Most failures turn out to be search failures.

**Interview follow-up**: "Answers are wrong for questions about tables — what do you do?" Check whether the table survived parsing and chunking, by printing the chunk. That's usually where it broke.

---

### Case C: Daily risk report commentary
**Goal**: every morning, produce a short written summary of the risk report, such as the biggest changes in rate sensitivity by desk and any limit breaches.

**Design: a fixed workflow, not a free agent**
1. Code computes every number: profit and loss, rate sensitivity by tenor, limit usage, the largest changes since yesterday.
2. Code passes those numbers to the model as a table, and the model *only writes the words*.
3. Code checks every number in the model's text against the input table. Any number that doesn't match blocks the report.
4. A person reviews and sends the report.

**Tricks**
- Never ask the model to calculate, for example "compute the change". Give it the change already calculated.
- Put the direction into the data ("increased" or "decreased") so the model can't flip a sign.
- Give two or three past reports that people liked as style examples.
- Keep a log of the input, the output and the reviewer's edits. The edits become test cases.

**Interview point**: this shows judgment. The model is used where it adds value (writing) and kept away from where it adds risk (numbers).

---

### Case D: An MCP server for market data (for example over a kdb+ tick database)
**Goal**: let an internal assistant answer questions like "What was the average bid–ask spread in 10-year swaps between 2 and 3 p.m. yesterday?"

**Tool design**
- Offer **specific tools** rather than a raw "run any query" tool:
  `get_quotes(instrument, start, end, max_rows)`, `get_trades(...)`, `spread_stats(instrument, start, end, bucket_minutes)`.
  Specific tools are safer, cheaper and easier for the model to use correctly.
- If you do offer a raw query tool, make it **read-only**, with a time limit, a row limit and a list of allowed tables.
- **Return summaries, not raw rows**: 50,000 quote rows would swamp the model's context. Return statistics plus a small sample, or save the full result to a file and return the file path.
- Write **tool descriptions as documentation for the model**: units ("spread in basis points", where one basis point is 0.01%), the time zone, and an example call.
- **Clear errors**: "instrument 'USD10Y' not found; did you mean 'USD_SOFR_10Y'?" lets the model correct itself.

**Security notes**
- The server runs with a read-only service account, never with the user's full rights.
- Log every call: who asked, the query and the number of rows returned.
- Only install MCP servers from sources you trust. A tool's description is text the model reads, so a malicious one can carry hidden instructions.

---

### Case E: Pulling structured details out of client chat messages
**Goal**: salespeople get requests in chat, such as "can u show me a 5y payer, 50mm, spot start?". Turn each one into a structured order ticket.

**Design**
- Use a fixed output format: product, tenor, direction (pay or receive fixed), notional amount, start date, client. The text "50mm" means 50 million in trading slang, and the model must turn it into 50,000,000.
- **Check against reference data**: the tenor must be a valid one, the client must exist, and the notional must be within normal size. Anything that fails is flagged, never auto-filled.
- **A person confirms** every ticket before anything is booked or priced. The model saves typing; it never makes the decision.
- Collect corrections and turn them into test cases. Common errors: "mm" vs "m", the sign of "pay" vs "receive", and dates in different formats.

---

### Case F: Coding agents for research work
**Goal**: use a coding agent (an AI that can read and edit your code and run commands) to speed up research code: data loading, backtests, plots.

**What works**
- A short instruction file in the repository explaining how to run the tests and what the conventions are. This repo's `CLAUDE.md` is an example.
- **Tests as guard rails**: ask the agent to write a test against a known answer first (put–call parity, a closed-form price), then the code. The test catches silent mistakes.
- Small, reviewable changes. Read every change before you keep it.
- Run the agent in a restricted environment without production credentials.

**What to watch for**
- Code that runs but is subtly wrong: wrong day-count convention, off-by-one in dates, using today's data to make today's decision (look-ahead).
- A function that doesn't exist in the library ("invented" methods). Running the tests catches these.

---

## Part 3 — Practical tricks

### Prompting
- **Put the data first and the question last** in long prompts. Models answer more accurately that way.
- **Use tags** like `<document>…</document>` and `<question>…</question>` to keep instructions separate from data. This also reduces prompt injection.
- **Ask for evidence**: "quote the sentence that supports each claim". It reduces invented answers, and code can check the quotes.
- **Give the model a way out**: "if the information isn't there, say 'not found'". Without that, models tend to guess.
- **Explain why, not just what**: "be brief because traders read this on their phones" works better than "be brief".
- **Show examples of good output** rather than long lists of rules.

### Tool and agent design
- **Fewer, clearer tools beat many overlapping ones**. If two tools look similar, the model will mix them up.
- **Make tools safe to repeat**: a retry shouldn't book a trade twice.
- **Return short results**, and put big results in files.
- **Set a step limit and a budget** for every agent run, and stop with a clear message when hit.
- **Plan, then act**: for long tasks, have the model write a short plan first. It is easier to check and to resume.
- **A person approves anything irreversible**: sending emails, booking, deleting.

### Evaluation
- **Start with 20–50 real examples** before building anything fancy. Grow the set with every bug you find.
- **Look at failures by hand**. Reading 20 bad outputs teaches more than any single score.
- **Model graders need checking too**: when one model grades another, compare its grades with a person's on a sample first.
- **Re-run the full test set** whenever you change the prompt, the model or the search settings.

### Cost and speed
- **Reuse the fixed part of the prompt** (prompt caching) by putting instructions and documents first.
- **Batch anything that isn't urgent**. Batch processing is much cheaper.
- **Use smaller, cheaper models for simple steps** (routing, classification) and the strongest model for hard reasoning. Measure before switching.
- **Limit output length**. Output tokens are the slowest and most expensive part.
- **Stream long answers** so users see text as it is written.

### Debugging
- **Log the full prompt** that was actually sent, after templates and search results are filled in. Most bugs are visible there: a missing document, a wrong date or a cut-off table.
- **Check search before blaming the model**: was the right passage even in the prompt?
- **Reproduce with the exact model version and settings**.
- **Change one thing at a time**, and re-run the test set.

---

## Part 4 — Talking about it in interviews

**Describe a project with this structure**
1. **Problem**: who needed what, for example "traders spent 30 minutes a day searching term sheets".
2. **Why an LLM**: and why not a simpler tool.
3. **Design**: data, search, prompt, checks, and where a person stays involved.
4. **How you measured it**: a test set, numbers before and after.
5. **What went wrong and what you changed**: interviewers value this most.
6. **Risk and controls**: data handling, logging, approvals.

**Questions to expect, with short answers**
- *"How do you stop it making things up?"* Answer only from retrieved documents, require citations, check the citations in code, and allow "not found".
- *"How do you handle numbers?"* Code computes them, the model only writes the words, and code checks every number in the output.
- *"Would you put an LLM in the trading loop?"* Not in the fast path: it's too slow and not deterministic. It's fine offline, for slow signals, or as an assistant with a person in charge.
- *"How do you test for look-ahead bias?"* Hide names and dates, test only on periods after the training cutoff, and use timestamps for when information became available.
- *"Build your own model or use an existing one?"* An existing strong model plus your own data, almost always. BloombergGPT is the usual cautionary example.
- *"What would you log?"* The prompt, the model version, the retrieved documents, the output, the user, the timestamp, and any reviewer edits.
