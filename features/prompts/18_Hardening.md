# LLM Wiki Hardening & Portability

## Objective
Harden the LLM Wiki template/engine repo by fixing the broken `/split` command, eliminating duplicated link-resolution logic, wiring up the orphaned `review_scope.py`, normalising the Windows Python launcher, making bootstrap non-blocking, fixing the chart output path, and adding the `/retry` feature for failed inbox URLs.

## Context
Read "D:\my-2nd-brain\features\specs\2026-05-29-llm-wiki-hardening-design.md" spec and related "D:\my-2nd-brain\features\plans\2026-05-29-llm-wiki-hardening.md" implementation plan.
Detailed aspects of the actual implementation must be inferred by analyzing the codebase.

---

**Planning Phase Required:**
1. Review design spec and implementation plan
2. Create detailed plan before implementation
3. Get plan approval before coding
4. Use superpowers:subagent-driven-development to implement this plan. Remember to keep backlog.md tasks updated.