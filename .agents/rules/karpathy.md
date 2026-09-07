# Rule: Karpathy Coding Discipline

## Metadata
- **name**: karpathy-discipline
- **description**: Enforces Andrej Karpathy's guidelines for AI coding agents to prevent overengineering and silent assumptions.
- **glob**: "**/*"

## Rule Description
This rule ensures the agent remains disciplined, avoids silent assumptions, keeps changes surgical, and values simplicity.

### Guidelines
1. **No Assumptions**: If any requirement is underspecified, the agent MUST stop and ask the user for clarification.
2. **Simplicity First**: Write the minimum amount of code to solve the problem. Do not design for speculative future requirements.
3. **Surgical Changes**: Do not refactor adjacent code or modify comments unrelated to the task. Keep git diffs as minimal and clean as possible.
4. **Verification**: Always run verification steps (like unit tests or compiling/building the app) to ensure no regressions.
