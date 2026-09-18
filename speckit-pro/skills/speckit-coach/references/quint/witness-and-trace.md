<!-- Derived from Quint LLM Kit at commit cc75369f741af7d490936f82002c2d28e3b3d78d.
Upstream files:
- agentic/agents/verifier.md
- agentic/commands/verify/generate-witness.md
- agentic/commands/verify/explain-trace.md
- agentic/commands/verify/debug-witness.md
This is a SpecKit adaptation, not a verbatim upstream copy.
-->

# Quint witnesses and trace explanations

SpecKit uses witnesses as authoring aids before `formal-check`, and Apalache as
the actual checker. A witness proposal must stay subordinate to the approved
requirements, model configuration, bounds, and evidence level. Do not install
tools or run checker commands from the model-author surface.

| Check | Purpose | Expected outcome | Failure meaning |
|---|---|---|---|
| Witness | Prove that an important action, state, or transition is reachable | The negated goal is violated | The path may be unreachable, over-constrained, rare, or need a larger bound |
| Invariant | Show that a required safety condition holds | No violation within the declared bound | A safety defect or a model error |

## Propose witnesses

- Prefer one witness for each major action, plus one for each consequential state
  or transition requested by the approved requirement.
- Use the smallest path that reaches the goal.
- Make each witness name and requirement explicit in the catalog.
- Do not invent temporal or fairness properties that the selected mode does not
  check.
- Do not use a witness pass or failure to claim exhaustive exploration.

## Interpret results

- A witness violation is good when the goal was reachability.
- A satisfied witness may mean the model is too constrained, the path is rare,
  or the declared bound/budget is too small.
- An invariant violation is a safety finding, not a witness success.
- A timeout or inconclusive result is not a pass and does not imply either
  reachability or safety.

## Explain counterexamples

For a safety counterexample, describe:

1. the approved rule that is false in the final state;
2. the variables that make it false;
3. the transition sequence that produced those variables;
4. whether the issue is a model error, a requirement conflict, or a real design
   defect.

For a witness, explain what state was reached, which actions produced it, and
which approved requirement it supports.

## Debug unreachable witnesses

Work from the smallest evidence first:

1. Confirm the witness goal and its dependency chain.
2. Find actions that write the goal variables.
3. Inspect guards around those writes.
4. Test whether the goal is structurally impossible, rare, or blocked by an
   over-tight precondition.
5. If a relaxation is needed, propose it to the parent; do not weaken a real
   requirement.

Do not convert a sampled trace into an exhaustive proof, and do not report a
simulation as implementation conformance. For implementation traces, use
[implementation-traces.md](../implementation-traces.md).
