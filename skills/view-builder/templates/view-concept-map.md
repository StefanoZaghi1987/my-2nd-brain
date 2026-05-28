---
type: view
kind: concept-map
created: {{DATE}}
updated: {{DATE}}
shareable: false
based_on:
  - [[wiki/pages/{{TOPIC}}]]
purpose: "Visual map of how the key concepts in {{TOPIC}} connect."
---

# Concept map: {{TOPIC_TITLE}}

```mermaid
graph TD
    A[Central concept] --> B[Sub-concept 1]
    A --> C[Sub-concept 2]
    B --> D[Detail]
    C --> E[Detail]
    B -.related.- C
```

<details>
<summary>Text fallback</summary>

<!-- Populate this list with the same nodes and edges as the Mermaid diagram above.
     Format: - Source Node → Target Node
     Both blocks must remain in sync — same nodes, same directed edges. -->

- {{Node A}} → {{Node B}}
- {{Node A}} → {{Node C}}

</details>

**Legend:** solid arrows = direct dependency, dotted lines = related.

## Linked pages

- Central: [[wiki/pages/{{TOPIC}}]]
- Sub-concepts: [[wiki/pages/...]]

## Notes

- Update when new concepts emerge.
- If the map grows past ~12 nodes, split into two views.
