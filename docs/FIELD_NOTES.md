# Field Notes: Building a 3-Second Scam Shield for the Moment Before Harm

Scam detection is often framed as a classification problem: a message goes in,
a probability comes out, and the technical work appears complete.

That framing misses the moment in which consumer fraud succeeds.

A person is on the phone with someone claiming to be the bank. A text says a
package cannot be delivered. A family member appears to have a new number and
needs money immediately. The recipient is not calmly comparing model scores.
They are under pressure and deciding whether to click, pay, or reveal a code.

The scale is difficult to ignore. The Federal Trade Commission says consumers
reported more than $12.5 billion in fraud losses in 2024, while the FBI recorded
$4.885 billion in reported losses from 147,127 complaints by people over 60.
Those numbers describe reported harm. They do not capture the fear, shame, and
loss of confidence that can follow it.

Scam Court AI began as a small courtroom that explained suspicious messages.
Building and testing the experience changed the product thesis:

> Give one safe action in three seconds. Put the evidence on trial afterward.

## The First Version Put the Court First

The original concept was memorable: paste a suspicious message and watch a
Detective, Prosecutor, Defender, and Judge examine it.

The metaphor worked. It separated evidence from accusation and made uncertainty
visible. But the interaction had the wrong priority. A user had to read the
case before learning what to do.

For someone under pressure, the first sentence must be behavioral:

- hang up;
- do not click;
- do not share the code;
- call the relative using a saved number;
- open the official app yourself.

The court still matters, but only after the user has permission to pause.

## The Shift to the 3-Second Shield

Shield Mode reversed the original sequence:

1. `STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK`
2. one immediate action
3. one trusted-contact script
4. evidence and full courtroom explanation

This was more than a visual redesign. It created a product-level safety
contract.

If the system does not have usable evidence, it cannot return low visible risk.
If a message contains a link or requests an account action, the safe default is
independent verification. If a caller asks for money, a password, or an OTP
under pressure, the action is to stop.

The phrase `LOW VISIBLE RISK` is intentional. It does not mean safe. It means
the current evidence did not expose a strong signal.

## Why Awareness Is Not Enough

Most people know scams exist. The harder question is:

> What should I do with this message right now?

Scammers exploit context rather than ignorance. They borrow carrier names,
banking language, familiar payment tools, family relationships, and urgent
deadlines. They create a narrow decision window before the recipient can ask
someone else.

That is why Scam Court AI is not designed as an open-ended chatbot. It is a
safety pause with a constrained output vocabulary and a visible fallback
policy.

## Why Pasted Text Was Not Enough

Pasted text is useful for development and private local analysis, but it is a
weak assumption for the users and situations we care about.

Suspicious evidence often arrives as:

- screenshots forwarded by a family member;
- image-based invoices;
- SMS or WhatsApp messages where copying is awkward;
- live phone calls where writing a detailed prompt is unrealistic.

The product expanded along three paths:

1. **Vision Witness** reads screenshots.
2. **Suspicious Call** asks five concrete warning-sign questions.
3. **Chrome Companion** brings a selected-text Shield result into the current page.

Each path still feeds the same safety philosophy: interrupt the dangerous
action first and expose the evidence second.

## MiniCPM-V Became the Vision Witness

Screenshot support needed to be real, not a decorative upload box. We chose
OpenBMB `openbmb/MiniCPM-V-4` for a bounded role:

- extract visible message text;
- classify screenshot context;
- identify visual risk clues;
- return confidence and provenance;
- prepare evidence for the text safety engine.

MiniCPM-V does not replace the policy. Its output becomes evidence for the
existing engine. This separation is important because OCR and multimodal
inference can fail.

The model is imported and initialized only when the vision backend is enabled
and a screenshot request arrives. On Hugging Face Spaces, the shared handler is
registered through `@spaces.GPU` for ZeroGPU. CPU-only startup remains
available with vision disabled.

When vision fails, screenshot-only input receives `VERIFY FIRST`. The
application discloses the failure instead of pretending the image was read.

## The Courtroom as an Explanation Contract

A red badge may interrupt a user once, but it does not teach them how the
decision was made. The courtroom divides the explanation into five jobs:

- The **Detective** lists visible evidence without deciding the case.
- The **Prosecutor** explains how that evidence fits manipulation patterns.
- The **Defender** tests plausible benign interpretations.
- The **Judge** weighs the record and assigns the policy verdict.
- The **Safety Clerk** converts the verdict into a safe action and next steps.

The Defender is essential. A safety system can become alarmist if it never
acknowledges innocent explanations. The product can show that uncertainty while
still requiring independent verification for links and sensitive actions.

These roles are backed by an exportable `CourtroomReport`, not just labels in
the interface. The report carries evidence, score, verdict, actions, model and
vision provenance, limitations, and the agent trace.

## Designing for Calm Authority

The interface went through several iterations. Early versions felt too close to
default Gradio or exposed too much explanation at once. Later visual work added
depth, but state and control architecture had to be stabilized before polish
could be trusted.

The final direction uses:

- large action-first verdicts;
- restrained dark graphite surfaces;
- amber for caution and evidence;
- red only for `STOP`;
- visible role emblems;
- a utility dock for language, theme, runtime, and API information;
- a full light palette rather than a simple inversion;
- large controls suitable for older adults and mobile use.

The lesson was straightforward: premium safety design is not decoration. It is
hierarchy, legibility, predictable state, and honest failure behavior.

## The Chrome Companion Privacy Boundary

The browser prototype is intentionally smaller than a conventional security
extension.

It does not scan the page. It does not read an inbox. It does not monitor
WhatsApp. It has no persistent content script.

The flow begins only after the user selects text and chooses **Take this to Scam
Court** from the context menu. Chrome provides that selection to the service
worker, which calls the named Gradio endpoint. The content script is injected
only to render the result.

If the API is unavailable, the extension does not guess. It shows
`VERIFY FIRST` and tells the user not to click links or share codes.

## Why False Reassurance Is the Primary Safety Failure

False positives are inconvenient. False reassurance can cause an irreversible
action.

A false low-risk result can encourage someone to:

- click a credential-harvesting link;
- send money, crypto, or a gift card;
- disclose a recovery code;
- continue a coercive call;
- trust an impersonated family member.

The evaluation format therefore includes `must_not_return_low_risk` as an
explicit guardrail. Package links, bank actions, OTP requests, money transfers,
impersonation, and ambiguous account actions are protected cases.

The runner checks:

- expected verdict;
- accepted score range;
- false `LOW VISIBLE RISK`;
- missed `STOP` decisions;
- backend errors;
- pass rates and average scores by category.

The current deterministic baseline passes 60 of 60 synthetic cases with zero
false-low-risk results and zero safety failures.

That is a regression baseline, not a real-world accuracy claim. The dataset is
synthetic, English-first, and deliberately balanced for policy coverage.

## What Codex Changed

Codex was used as an engineering collaborator across the product rather than as
a single-file generator. Its work included:

- stabilizing language, theme, and Gradio state updates;
- restoring the utility and API surfaces;
- integrating and validating the ZeroGPU execution path;
- preserving MiniCPM-V lazy loading and safe fallbacks;
- expanding tests and the 60-case evaluation suite;
- building and polishing the Chrome Companion prototype;
- producing architecture documentation and rendered diagrams;
- running browser-based visual QA and creating the public screenshot proof pack;
- preparing the final README, Field Notes, and submission copy.

The useful pattern was not “ask for an app.” It was iterative repository work:
inspect the implementation, make scoped changes, run the product, test the
safety contract, and verify the public artifact.

## Lessons Learned

### Action must precede explanation

The courtroom becomes useful only after the user knows whether to stop, verify,
or continue with normal caution.

### Failure states are product states

“Vision unavailable” or “API failed” cannot remain a debug detail. Each failure
changes the user-facing safety action.

### Small models benefit from explicit boundaries

MiniCPM-V handles screenshot evidence. The text backend handles analysis. The
policy handles conservative action. Narrow responsibilities make the system
easier to inspect and evaluate.

### A risk score is not a probability

The score orders policy severity. Presenting it as a calibrated probability
would overstate what the system knows.

### A memorable metaphor still needs a schema

The courtroom became credible when the roles wrote to a stable report that
could be exported, tested, and consumed by another interface.

### Public proof should be reproducible

Screenshots, architecture, tests, evaluation cases, and agent traces should let
a judge understand the product without relying on a pitch alone.

## Honest Limitations

- The evaluation set is synthetic and English-first.
- The heuristic engine can miss scams that avoid known patterns.
- Unusual legitimate messages may be over-flagged.
- MiniCPM-V can misread screenshots.
- Risk scores are not calibrated probabilities.
- The app does not check live domain reputation or sender identity.
- The Chrome extension is a prototype, not a Chrome Web Store release.
- The product is not a substitute for a bank, carrier, law-enforcement agency,
  lawyer, financial adviser, or cybersecurity professional.

The system cannot know that a message is safe. It can expose visible risk, slow
down dangerous actions, and make uncertainty harder to ignore.

## What Comes Next

- trusted-family-contact workflows with explicit consent;
- multilingual safety copy, patterns, and evaluation;
- human-reviewed adversarial and screenshot cases;
- a fine-tuned small model for structured safety reasoning;
- mobile SMS and active-call companion experiments;
- stronger browser integration and automated extension testing;
- a community-reviewed scam pattern library with versioned provenance.

## Sources

- [FTC: reported fraud losses reached $12.5B in 2024](https://www.ftc.gov/news-events/news/press-releases/2025/03/new-ftc-data-show-big-jump-reported-losses-fraud-125-billion-2024)
- [FBI IC3 Elder Fraud Report 2023](https://www.ic3.gov/AnnualReport/Reports/2023_IC3ElderFraudReport.pdf)
- [FBI IC3 Annual Report 2024](https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf)
