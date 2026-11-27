# Culture Fit

How trading and quant firms judge "fit", the questions they ask, how to structure answers, and the
mistakes that sink otherwise strong candidates. Fit is assessed in *every* round, not only the
behavioural one. Each term is explained the first time it appears; a glossary is at the end.

Related: the story bank and questions to ask in
[analytics-dev, sections 10–11](../analytics-dev/README.md#10-behavioural-round).

Contents:

1. [What "fit" means at a trading firm](#1-what-fit-means-at-a-trading-firm)
2. [Where they test it](#2-where-they-test-it)
3. [How to structure an answer](#3-how-to-structure-an-answer)
4. [Question bank: what each question is really asking](#4-question-bank-what-each-question-is-really-asking)
5. [Three worked answers](#5-three-worked-answers)
6. [Why trading, why this firm, why this role](#6-why-trading-why-this-firm-why-this-role)
7. [Fit signals inside technical rounds](#7-fit-signals-inside-technical-rounds)
8. [Red flags to avoid](#8-red-flags-to-avoid)
9. [Questions that show the right instincts](#9-questions-that-show-the-right-instincts)
10. [The day before](#10-the-day-before)
11. [Glossary](#11-glossary)

---

## 1. What "fit" means at a trading firm

Trading firms are usually small, flat and fast. A wrong number can lose money within minutes,
and people work closely across trading, research and engineering. So they look for:

| Trait | What it looks like | What they fear instead |
|---|---|---|
| **Ownership** | You follow a problem to its root cause and close the loop with whoever was affected | "Not my job", passing problems along |
| **Intellectual honesty** | "I don't know, but here's how I'd find out." You say when you are unsure and how sure you are | Bluffing, which is dangerous when money depends on the answer |
| **Humility, low ego** | You credit others, take feedback, and change your mind when shown evidence | Defending a wrong answer, blaming colleagues |
| **Curiosity** | You ask why markets or systems behave as they do; you learn outside your lane | Doing only what was specified |
| **Collaboration** | You explain clearly to traders and quants, and you listen to users | Hiding in code, talking down to non-specialists |
| **Calm under pressure** | Clear steps during an incident or a tough question | Panic, freezing, or reckless fixes |
| **Speed with rigour** | You ship fast, with tests and checks that catch your own mistakes | Either slow perfectionism or careless speed |
| **Risk awareness** | You ask "what could go wrong, and how bad would it be?" | Optimism about edge cases |
| **Long-term thinking** | You build things others can maintain; you want to grow at the firm | Short-term hacks; job-hopping signals |

A useful mental model: **would they trust you with the production system at 7 a.m. before the
market opens, and would they enjoy sitting next to you every day?**

---

## 2. Where they test it

- **The behavioural interview**: past-experience questions ("tell me about a time...").
- **Technical rounds**: how you take hints, admit mistakes, explain your thinking and test your code (section 7).
- **Conversations with traders or desk users**: can you talk to them in their language, briefly and with numbers?
- **The questions you ask**: they show what you care about (section 9).
- **Informal moments**: lunch, walking between rooms, chatting with the recruiter. Treat everyone the same, including the receptionist.
- **References and how you talk about past employers**: never negative.

---

## 3. How to structure an answer

**STAR**: Situation, Task, Action, Result.

| Part | Length | Content |
|---|---|---|
| Situation | 1–2 sentences | Context: team, system, stakes. Use numbers ("risk for 40,000 positions, needed by 6 a.m.") |
| Task | 1 sentence | What *you* were responsible for |
| Action | 60% of the time | What you did, step by step, and *why*. Say "I", not "we", for your part |
| Result | 1–2 sentences | Measured outcome ("run time down from 2 hours to 15 minutes; no misses since") |
| Lesson | 1 sentence | What you'd keep or change. This shows you reflect |

Rules:
- **Two minutes**, then stop. They will ask follow-ups if they want more depth.
- **Numbers first.** Trading people think in numbers: time saved, error rates, money, users affected.
- **Be specific.** One real incident beats a general description of how you usually work.
- **Be honest about your part.** Saying "the team designed it; I built the caching layer" is more believable than taking all the credit.
- **Have a failure story you can tell comfortably.** Everyone has one; not having one is a red flag.

---

## 4. Question bank: what each question is really asking

| Question | What they are really asking | Answer with |
|---|---|---|
| Tell me about yourself. | Can you summarise yourself in 90 seconds, relevant to this job? | Present (current role, one key achievement) → past (how you got here) → future (why this role) |
| Tell me about a project you're proud of. | Depth, ownership, impact | Your best technical story; know every detail, because they will dig |
| Tell me about a time something broke in production. | Calm, method, ownership, learning | Incident story: mitigate, diagnose, fix, post-mortem |
| Tell me about a mistake you made. | Honesty, humility, learning | A real mistake with real consequences, what you did right after, and what changed |
| Describe a disagreement with a colleague. | Do you handle conflict with evidence, not ego? | Disagreed on design; gathered data or prototyped; agreed or "disagreed and committed" |
| Tell me about a difficult user or stakeholder. | Empathy, communication | A trader or manager with urgent demands; you understood the real need and set expectations |
| When did you have to learn something fast? | Curiosity, speed of learning | A new domain or language; how you learned (sources, people, small experiments) |
| Tell me about a time you went beyond your role. | Ownership | Fixed something no one owned; told the owners |
| How do you prioritise when everything is urgent? | Judgment | Impact × urgency; ask the stakeholders; communicate what slips |
| Tell me about feedback that was hard to hear. | Humility | Specific feedback, your first reaction, what you changed |
| What would your last manager say you need to improve? | Self-awareness | A real weakness, with evidence you are working on it (not "I work too hard") |
| Why are you leaving your current job? | Are you running away, or towards something? | Towards: closer to markets, harder problems, more ownership. Never criticise |
| Why trading? Why this firm? Why this role? | Have you thought about it, or are you applying everywhere? | Section 6 |
| Where do you see yourself in five years? | Will you stay and grow? | Deeper expertise in this area, more ownership, mentoring others |
| What do you do outside work? | Are you a curious, rounded person? | Something real; competitive games, puzzles and sports go down well, but only if true |
| Do you have questions for us? | Interest and judgment | Section 9. Never "no" |

---

## 5. Three worked answers

These are templates: replace the bracketed parts with your own facts. Do not memorise them word
for word; memorise the *structure* and the numbers.

**"Tell me about a time something broke in production."**
> **S**: At [company], I owned [the end-of-day risk job] that [risk managers] used at [7 a.m.]. One morning the job finished, but [the DV01 for one desk was ten times yesterday's].
> **T**: I was on call, so I had to decide quickly whether the numbers could be used.
> **A**: First I told the users the numbers for that desk were suspect and should not be used, so nobody acted on them. Then I compared the inputs to the previous day: positions matched, but [one curve point was missing and had been filled with zero]. I re-ran the desk with [the previous day's curve point, clearly flagged] so they had usable numbers by [7:30]. After the market data team fixed the feed, I re-ran it properly.
> **R**: Users had correct numbers within [40 minutes] and no decisions were made on bad data. I then added [a check that refuses to build a curve with missing points] and an alert, and it has caught [two] similar problems since.
> **Lesson**: tell users first, then fix; and every incident should leave behind a test or an alert.

**"Tell me about a mistake you made."**
> **S/T**: I [changed a date-handling function] to fix [a bug], and my change passed the tests.
> **A**: The next day [a report for a non-US market was wrong], because [the holiday calendar logic depended on the old behaviour]. I told my manager straight away, rolled the change back, and found that our tests only used US dates. I added tests for [three other calendars], fixed the change properly and re-released it.
> **R**: The report was wrong for [one day], it was caught before [month-end], and the new tests have since caught [another bug].
> **Lesson**: I now look at who *calls* the code I change, not only the code itself, and I write tests for the edge cases before I change anything.

**"Describe a disagreement with a colleague."**
> **S**: A senior colleague wanted to [rewrite the pricing service in another language] to make it faster; I thought [caching] would get most of the gain at far less risk.
> **A**: Rather than argue, I suggested we measure. I profiled one day's run: [80%] of the time was [rebuilding the same curves]. I built a small caching prototype in [two days], which cut the run from [2 hours] to [25 minutes]. I showed both of us the numbers.
> **R**: We shipped the caching first, and kept the rewrite on the roadmap for the part that was still slow. My colleague later [reviewed and improved] the cache design.
> **Lesson**: evidence settles design arguments faster than opinions, and you should keep the relationship in mind: the goal was the system, not winning.

---

## 6. Why trading, why this firm, why this role

**Why trading?** Pick two or three that are true for you:
- Fast feedback: your work affects P&L and risk every day, and you see whether it was right.
- Hard problems combining maths, data and engineering, often with real constraints (latency, correctness, scale).
- Small teams and direct contact with users (traders, risk managers), with real ownership.
- A culture where being right matters more than titles.

**Why this firm?** Research before the interview (from public sources only):
- **What it trades**: asset classes, venues, styles (market making, relative value, options).
- **Its technology**: engineering blog posts, conference talks, open-source projects, the languages in job ads.
- **How it describes itself**: values or careers pages; what interviewers say about the team.
- **The team**: what this team builds and who uses it (from the job description and the recruiter).

Then connect three things: *what they do* + *what you have done* + *what you want to learn*.
Example structure: "You [trade rates and options across many venues], and this team builds the
[analytics risk managers use every day]. I've built [risk and P&L tools] and want to be closer to
the trading decisions, with [more complex products and real-time constraints]."

**Why this role?** Point to specific lines in the job description and match each to a piece of your experience.

---

## 7. Fit signals inside technical rounds

| Do | Why it matters |
|---|---|
| Think aloud and state assumptions | Shows how you would work with a colleague |
| Ask clarifying questions before coding | You would ask the trader what they really need |
| Start simple, then improve | Speed with rigour |
| Take hints gracefully and use them | Coachable, low ego |
| Say "I'm not sure; my guess is X because Y" | Intellectual honesty, with a calibrated level of confidence |
| Find and fix your own bug by testing | Ownership of correctness |
| Admit when you've gone down a wrong path, and back out | Calm, honest |
| Mention production concerns (edge cases, monitoring, failure modes) | You have run real systems |

Interviewers often remember *how* you reacted when stuck more than whether you finished.

---

## 8. Red flags to avoid

- Criticising a past employer, manager or colleague, even if it is deserved.
- "We did..." for the whole story, so they can't tell what *you* did.
- Stories with no numbers, no conflict and no lesson.
- Not having a failure story, or a fake weakness ("I'm a perfectionist").
- Bluffing on a technical question rather than saying you don't know.
- Arguing with the interviewer about a hint, or about whether a question is fair.
- Interest only in pay, hours or title, especially early in the process.
- No questions at the end, or questions answered on the firm's website.
- Arrogance about a past firm or school, or dismissing traders or operations staff.
- Talking for five minutes without checking whether they want more.

---

## 9. Questions that show the right instincts

Ask two or three per interviewer, tuned to who they are:

- **To an engineer**: "What does a good first six months look like on this team?" "How do you test analytics, and how do you know a number is right?" "What was the last significant incident, and what changed after it?"
- **To a trader or risk manager**: "Which numbers do you look at first each morning, and what makes you distrust one?" "What would you like the platform to do that it can't today?"
- **To a manager**: "How do you give feedback, and how often?" "What separates the people who do very well here?" "How are priorities set between desks that all want something?"
- **To anyone**: "What surprised you most when you joined?" "What do you enjoy most about working here?"

Avoid opening with pay, hours or remote work. Those belong with the recruiter or come at the offer stage.

---

## 10. The day before

- [ ] Six STAR stories written down, each with numbers and a lesson, said out loud at least twice ([story bank](../analytics-dev/README.md#10-behavioural-round)).
- [ ] A 90-second "tell me about yourself".
- [ ] "Why trading / this firm / this role" answers linked to the job description.
- [ ] Three facts about what the firm trades and the team builds.
- [ ] Two or three questions per interviewer type.
- [ ] Know every line of your CV well enough to go two levels deeper on each.
- [ ] For video interviews: camera, sound, a quiet room, water, paper and pen.
- [ ] Sleep. A tired brain does worse on brainteasers than an unprepared one.

---

## 11. Glossary

| Term | Meaning |
|---|---|
| Behavioural question | "Tell me about a time when...": asks about past behaviour to predict future behaviour |
| Calibrated confidence | Saying how sure you are, and being right about that often |
| Disagree and commit | Stating your disagreement, then fully supporting the decision once it is made |
| Ownership | Taking responsibility for a problem until it is solved, whoever caused it |
| Post-mortem | A written review after an incident: what happened, why, and what changes |
| STAR | Situation, Task, Action, Result: a structure for behavioural answers |
| Stakeholder | Anyone affected by or depending on your work (traders, risk managers, other teams) |
