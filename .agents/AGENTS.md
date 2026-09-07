# Workspace Rules for Anki AI Learning Hub

Strictly follow these rules whenever developing, updating, or testing in this workspace:

## 1. Project Overview & Architecture
`Anki_AI_Learning_Hub` is an AI-powered language learning system for Anki Desktop, integrating 8 interactive game modes powered by Google Gemini API.
- **Frontend SPA**: HTML5, CSS3 Glassmorphism, and Vanilla JS in `web/`.
- **Bridge Layer**: Asynchronous IPC bridge in `web/js/bridge.js` communicating with `core/engine.py`.
- **Core Domain**: `core/` contains pure domain logic, PromptManager, SchemaRegistry, i18n catalog, Logger, and Constants.
- **LLM Layer**: `llm/gemini.py` implements a 6-Tier Waterfall failover engine (`gemini-3.5-flash-lite` -> `gemini-flash-lite-latest` -> `gemini-3.5-flash` -> `gemini-3.6-flash` -> `gemini-3.1-flash-lite` -> `gemini-3-flash-preview`), key rotation, and exponential backoff.
- **Gamemodes**: `gamemodes/` contains handlers for the 8 game modes: FillBlank, Cloze, Translation, Unscramble, WordMatching (Offline), StoryGenerator, SentenceTransform, and Taboo.

## 2. Mandatory Rules & Discipline
- **User Confirmation (`user_confirmation.md`)**: ALWAYS stop and obtain explicit user approval before modifying data or architecture.
- **Karpathy Minimalist Coding (`karpathy.md`)**: Surgical, minimal edits. Zero assumptions without empirical verification.
- **Ponytail Lazy Senior Dev (`ponytail.md`)**: Efficient minimalism (YAGNI, standard library first, shortest working diff).
- **Clean Code (`clean_code.md`)**: Python PEP8, complete type hints, robust exception handling, structured flow logging.
- **Git Governance (`git-conventions`)**: Branching strategy (`feat/`, `fix/`, `refactor/`), Atomic Conventional Commits (`<type>(<scope>): <summary>` + *Why*).
- **Two-Phase Approval Gate**: Phase 1 Plan & Log in `plans/current/` -> HARD STOP -> User approval -> Phase 2 implementation.
- **Test-Driven Verification**: Every change must maintain 100% pass rate on `python -B -m unittest discover -s tests -p "test_*.py" -v` (65/65 tests) and browser/E2E validation via `playwright-mcp`.

## 3. Skills Directory Index (17 Skills in `.agents/skills/`)

### A. Workflow & Planning (`_shared`)
| Skill | Path | Activation Trigger |
| :--- | :--- | :--- |
| **`spec-driven-development`** | `.agents/skills/spec-driven-development/SKILL.md` | Feature planning, SDD specs, constitution, acceptance criteria. |
| **`superpowers-methodology`** | `.agents/skills/superpowers/SKILL.md` | Disciplined workflow: Design -> Plan -> TDD -> Implement -> Review. |
| **`brainstorming`** | `.agents/skills/brainstorming/SKILL.md` | Solution design trade-offs, architecture options alignment. |
| **`task-generation`** | `.agents/skills/task-generation/SKILL.md` | Decomposing complex requirements into bite-sized tasks (<100 LOC). |
| **`visual-explainer`** | `.agents/skills/visual-explainer/SKILL.md` | Mermaid architecture diagrams, data flow charts. |

### B. Core, Backend & Anki Engine (`code / core`)
| Skill | Path | Activation Trigger |
| :--- | :--- | :--- |
| **`system-programming`** | `.agents/skills/system-programming/SKILL.md` | Backend architecture, API design, data pipelines, error handling. |
| **`coding-discipline`** | `.agents/skills/coding-discipline/SKILL.md` | Robust error handling, flow JSONL logging, regression prevention. |
| **`git-conventions`** | `.agents/skills/git-conventions/SKILL.md` | Branching naming, Conventional Commits, PRs, and release workflows. |
| **`cefr-topic-classifier`** | `.agents/skills/cefr-topic-classifier/SKILL.md` | CEFR level matching (A1-C2), IELTS topic clustering. |
| **`anki-connect-engine`** | `.agents/skills/anki-connect-engine/SKILL.md` | AnkiConnect API, backup, card packaging. |

### C. Frontend, UI/UX & Design (`design / web`)
| Skill | Path | Activation Trigger |
| :--- | :--- | :--- |
| **`ui-ux-pro-max`** | `.agents/skills/ui-ux-pro-max/SKILL.md` | UI/UX design intelligence, Glassmorphism, interaction states, accessibility tokens. |
| **`svg-icon-engineering`** | `.agents/skills/svg-icon-engineering/SKILL.md` | Clean SVG vectors, `currentColor` adoption, Dark/Light mode theme icons. |
| **`web-accessibility-wcag`** | `.agents/skills/web-accessibility-wcag/SKILL.md` | WCAG 2.2 AA standards, keyboard navigation (Tab/Enter), modal focus traps. |
| **`anki-report-visualizer`** | `.agents/skills/anki-report-visualizer/SKILL.md` | Visual dashboard generation, Chart.js analytics. |

### D. Testing & Quality Assurance (`testing`)
| Skill | Path | Activation Trigger |
| :--- | :--- | :--- |
| **`automated-testing`** | `.agents/skills/automated-testing/SKILL.md` | Unit testing, mock APIs, regression test suites (Python unittest). |
| **`playwright-mcp`** | `.agents/skills/playwright-mcp/SKILL.md` | On-demand browser E2E automation, DOM & form validation, game flow verification. |
| **`front-end-checklist`** | `.agents/skills/front-end-checklist/SKILL.md` | Pre-launch frontend checklist (385 rules): a11y, performance, memory leaks. |

## 4. Build & Anki Sync Commands
- Run Tests: `python -B -m unittest discover -s tests -p "test_*.py" -v`
- Build Packages: `python scripts/build_addon.py`
- Sync to Anki: Copy clean files to `%APPDATA%\Anki2\addons21\AI_Learning_Hub\`
