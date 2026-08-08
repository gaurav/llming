# VLMD diff

- **base** — `tests/fixtures/base.json`
- **revised** — `tests/fixtures/revised.json`

5 variables in common, 1 added, 1 removed. 5 of the shared variables differ, in 20 field-level changes across 17 distinct old → new patterns.

## Document-level properties

| property | from | to |
|---|---|---|
| `description` | *(absent)* | `"Converted from redcap format to HEAL VLMD schema v0.3.2. Study ID: EX00001"` |
| `title` | `"Example Data Dictionary: ../input/example.redcap.csv"` | `"An Example Study of Something"` |

## Variables added (1)

<details><summary><code>CONSENTDAT</code></summary>

```json
{
  "custom": {
    "Text Validation Type OR Show Slider Number": "date_mdy"
  },
  "description": "A variable the LLM tool added.",
  "name": "CONSENTDAT",
  "section": "Demographics",
  "type": "string"
}
```

</details>

## Variables removed (1)

<details><summary><code>RETIRED</code></summary>

```json
{
  "description": "A variable the LLM tool dropped.",
  "name": "RETIRED",
  "section": "Demographics",
  "title": "A variable the LLM tool dropped.",
  "type": "string"
}
```

</details>

## Changed properties

### `enumLabels` — 3 variables, 2 distinct changes

- **2 variables** — `{"0": "False", "1": "True"}` → *(absent)*
  <details><summary>variables</summary>

  `AWAKE`, `WEAR`

  </details>

- **1 variable** — `{"0": "No pain", "10": "Worst possible pain"}` → `{"0": "No pain", "1": "", "10": "Worst possible pain", "2": "", "3": "", "4": "", "5": "", "6": "", "7": "", "8": "", "9": ""}`
  - `PAINSCORE`

### `description` — 3 variables, 3 distinct changes

| variable | from | to |
|---|---|---|
| `PAINSCORE` | `"Secondary outcome: worst pain in the last 24 hours"` | `"worst pain in the last 24 hours"` |
| `VISITDAT` | `"demographics: date of visit"` | `"date of visit"` |
| `site` | `"demographics: Site(blinded)"` | `"Site(blinded)"` |

### `constraints` — 2 variables, 1 distinct change

- **2 variables** — `{"enum": ["0", "1"]}` → `{"enum": ["True", "False"]}`
  <details><summary>variables</summary>

  `AWAKE`, `WEAR`

  </details>

## Appendix: conversion-tool conventions

These properties differ because the two tools that produced these files write metadata differently, not because the content was edited. They are listed so their uniformity can be confirmed, then skipped.

### `custom` — 5 variables, 5 distinct changes

| variable | from | to |
|---|---|---|
| `AWAKE` | *(absent)* | `{"Field Note": "Whether the participant was awake."}` |
| `PAINSCORE` | *(absent)* | `{"Text Validation Type OR Show Slider Number": "integer"}` |
| `VISITDAT` | *(absent)* | `{"Text Validation Type OR Show Slider Number": "date_mdy"}` |
| `WEAR` | *(absent)* | `{"Field Note": "Whether the device was being worn."}` |
| `site` | *(absent)* | `{"Section Header": "demographics"}` |

### `title` — 5 variables, 5 distinct changes

| variable | from | to |
|---|---|---|
| `AWAKE` | `"Whether the participant was awake."` | *(absent)* |
| `PAINSCORE` | `"Secondary outcome: worst pain in the last 24 hours"` | *(absent)* |
| `VISITDAT` | `"demographics: date of visit"` | *(absent)* |
| `WEAR` | `"Whether the device was being worn."` | *(absent)* |
| `site` | `"demographics: Site(blinded)"` | *(absent)* |

### `format` — 2 variables, 1 distinct change

- **2 variables** — `"any"` → *(absent)*
  <details><summary>variables</summary>

  `VISITDAT`, `site`

  </details>

