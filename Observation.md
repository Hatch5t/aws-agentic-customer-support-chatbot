# Observations

## Evaluation Run 1

The initial evaluation achieved a correctness score of 0.83,
following-instructions score of 0.50, and harmlessness score of 0.00.

The system prompt was refined to make the three routing behaviours
explicit and to clarify ambiguous cases.

The prompt also instructs the agent to collect missing bug-report
fields one at a time and to file a ticket immediately once all
required fields are available.

The evaluation results were reviewed at the individual prompt level
rather than relying only on the aggregate score.
