# Building a 3-Second Scam Shield for the Moment Before Harm

Scam detection is often presented as a classification problem. A message goes
in, a probability comes out, and the technical work appears complete.

That framing misses the moment in which consumer scams actually succeed.

A person is on the phone with someone claiming to be the bank. A text says a
package cannot be delivered. A family member appears to have a new number and
needs money immediately. The recipient is not calmly comparing model scores.
They are under pressure and deciding whether to click, pay, or reveal a code.

Scam Court AI started as a small courtroom that explained suspicious messages.
Testing the experience forced us to change the product. The explanation was
useful, but it arrived before the thing the user needed most: permission to
pause.

That led to the current design:

> Give one safe action in three seconds. Put the evidence on trial afterward.

## The Real User Problem

Older adults and non-technical family members are regularly told to "watch for
scams." That advice is correct but hard to apply. Modern scam messages borrow
real company names, plausible delivery language, familiar payment tools, and
urgent family stories.

The difficult question is not "What is phishing?" It is:

> "What should I do with this message right now?"

The first product requirement therefore became behavioral rather than
technical. The app had to interrupt momentum:

- stop the active call;
- avoid the message link;
- refuse the OTP request;
- contact the relative using a saved number;
- open the official bank or carrier app independently.

The risk score still matters, but it is not the first sentence.

## Why Pasting a Message Was Not Enough

The original interaction assumed the user could select and paste suspicious
text. That works for evaluation and development, but it is a weak assumption in
the situations we care about.

Scams often arrive as:

- screenshots forwarded by a family member;
- image-based invoices;
- WhatsApp or SMS conversations where copying is awkward;
- live phone calls where the user cannot safely write a detailed prompt.

We kept pasted text because it is fast and private, then added two paths around
its limitations:

1. **Vision Witness** reads screenshots.
2. **Suspicious Call** asks five concrete yes/no questions during a call.

The Companion Preview explores the next step: move the verdict closer to the
message through explicit selected-text integrations.

## The Shift to the 3-Second Scam Shield

Early versions led with the courtroom. The Detective, Prosecutor, Defender, and
Judge were memorable, but the user had to read too much before learning what to
do.

Shield Mode reversed the order:

1. `STOP`, `VERIFY FIRST`, or `LOW VISIBLE RISK`
2. one immediate action
3. one trusted-contact script
4. evidence and court explanation

This was not only a UI decision. It introduced a safety contract. If the system
did not have usable evidence, it could not return low visible risk. If a message
contained a link or requested an account action, the safe default became
independent verification.

The wording is intentional. `LOW VISIBLE RISK` does not mean "safe." It means
the current evidence did not expose a strong signal.

## Why a Courtroom?

A single red badge can protect a user once, but it does not teach them what
happened. The courtroom metaphor separates different kinds of reasoning:

- The **Detective** lists evidence without deciding the case.
- The **Prosecutor** explains how the evidence fits scam tactics.
- The **Defender** searches for an innocent interpretation.
- The **Judge** weighs both sides and records the decision.
- The **Safety Clerk** converts the decision into a safe action.

The Defender is important. Scam safety systems can become alarmist. Showing an
alternative explanation makes uncertainty visible while preserving the rule
that uncertain action requests should be verified independently.

The implementation emits a structured JSON report, so these roles are more
than decorative labels. The same evidence, verdict, action, and limitations can
be exported or consumed by a future integration.

## MiniCPM-V as the Vision Witness

Screenshot support had to do real work. We chose OpenBMB
`openbmb/MiniCPM-V-4` as a narrow Vision Witness:

- extract visible message text;
- classify the screenshot context;
- identify visual risk clues;
- prepare text for the existing safety engine.

MiniCPM-V does not replace the risk policy. Its output becomes evidence. This
separation matters because OCR or multimodal inference can fail.

The model is lazy-loaded only when the vision backend is enabled and a
screenshot arrives. On Hugging Face Spaces, the shared analysis handler is
decorated with `@spaces.GPU` for ZeroGPU. Local CPU mode can disable vision
without breaking startup.

When vision fails, screenshot-only input receives `VERIFY FIRST`. The failure is
reported, and the user is asked to paste text or verify through an independent
channel.

## Why False LOW VISIBLE RISK Is the Main Safety Failure

False positives are inconvenient. False reassurance can cause a person to take
an irreversible action.

A false low-risk result can encourage someone to:

- click a credential-harvesting link;
- send a payment or gift card;
- disclose a recovery code;
- continue a coercive phone call;
- trust an impersonated family member.

We therefore evaluate not only verdict accuracy but a dedicated
`must_not_return_low_risk` property. Package links, bank actions, OTP requests,
money transfers, and ambiguous account actions are protected cases.

The evaluation runner flags:

- verdict mismatches;
- scores outside the expected policy range;
- false `LOW VISIBLE RISK` results;
- missed `STOP` decisions;
- backend errors.

The current deterministic baseline passes 60 of 60 synthetic cases with zero
false-low-risk results and zero safety failures. That is a regression baseline,
not evidence of general real-world accuracy.

## Architecture

The system is deliberately layered:

1. Gradio collects text, screenshots, or call-checklist evidence.
2. A backend router selects the heuristic engine or optional SmolLM3 backend.
3. MiniCPM-V supplies screenshot evidence when enabled.
4. The safety policy applies conservative action rules.
5. `CourtroomReport` records evidence, agents, verdict, action, provenance, and limitations.
6. The UI renders Shield, Court, Call, and Companion views from the same result.

The default heuristic backend is deterministic and CPU-safe. The optional
SmolLM3 path falls back to that baseline if model loading or structured
generation fails. MiniCPM-V has a separate safe fallback.

This is less glamorous than a single end-to-end model call, but it makes
failure behavior explicit and testable.

## Evaluation Approach

The public dataset covers ten categories with six cases each:

- family impersonation;
- OTP/code theft;
- fake bank alerts;
- package delivery;
- marketplace deposits;
- fake invoices;
- government/refund/stimulus;
- romance/emergency money;
- safe benign messages;
- ambiguous action-required messages.

Each case defines an accepted verdict, score range, rationale, tags, and whether
low visible risk is forbidden. The same runner works locally and through an
optional Modal job.

The generated JSON report supports machine comparison. The Markdown report is
intended for human review and hackathon evidence.

## Lessons Learned

### Action must precede explanation

The courtroom is useful only after the user knows whether to stop, verify, or
continue cautiously.

### Failure states are product states

"Vision unavailable" cannot be a debug detail. It changes the safety verdict
and must be visible to the user.

### Small models benefit from explicit boundaries

MiniCPM-V handles screenshot evidence. The text backend handles structured
analysis. The policy handles conservative action. Narrow responsibilities make
the system easier to reason about.

### A risk score is not a probability

The score orders policy severity. Presenting it as a calibrated probability
would overstate what the system knows.

### A memorable metaphor still needs a contract

The court roles became credible when their outputs were included in a stable,
exportable report rather than existing only as UI copy.

## What Comes Next

- human-reviewed adversarial cases;
- multilingual scam patterns and evaluation;
- screenshot fixtures that measure OCR and visual reasoning;
- longitudinal evaluation across model and policy versions;
- accessibility testing with older adults;
- a privacy-first Chrome Companion using explicit selected text;
- stronger provenance and report signing for shared results.

## Honest Limitations

The current evaluation set is synthetic and English-first. The heuristic engine
will miss scams that avoid known patterns and may over-flag unusual legitimate
messages. MiniCPM-V can misread screenshots. The app does not check live domain
reputation or verify sender identity. The score is not a probability, and the
system is not a substitute for a bank, carrier, law-enforcement agency, or
security professional.

The most important limitation is also the reason for the product's conservative
design: Scam Court AI cannot know that a message is safe. It can expose visible
risk, slow down dangerous actions, and make uncertainty harder to ignore.
