# Agent Guide for Maze

> **Purpose**: Operational guide for agentic systems (Claude Code, mnemosyne orchestrators) working on the Maze adaptive constrained code generation project.

> **Scope**: Task classification, documentation updates, release management, repository organization, and quality assurance workflows.

> **Audience**: AI agents, automation systems, and developers using agentic workflows.

---

## Table of Contents

1. [Decision Trees](#1-decision-trees)
2. [Workflows](#2-workflows)
3. [Templates](#3-templates)
4. [Repository Tidying](#4-repository-tidying)
5. [Integration Points](#5-integration-points)
6. [Common Scenarios](#6-common-scenarios)
7. [Anti-Patterns for Agents](#7-anti-patterns-for-agents)
8. [Observability](#8-observability)
9. [Reference Tables](#9-reference-tables)
10. [Quick Command Reference](#10-quick-command-reference)
11. [Implementation Patterns](#11-implementation-patterns)
12. [Enforcement and CI/CD](#12-enforcement-and-cicd)

---

## 1. Decision Trees

### 1.1 Task Classification Tree

```yaml
task_classification:
  input: user_request

  decisions:
    - question: "Does request involve code changes?"
      yes:
        - question: "Is it a new feature?"
          yes:
            category: "feature"
            branch_prefix: "feature/"
            beads_type: "feature"
            changelog_section: "Added"
            workflow: "code_change_workflow"
          no:
            - question: "Is it a bug fix?"
              yes:
                category: "fix"
                branch_prefix: "fix/"
                beads_type: "bug"
                changelog_section: "Fixed"
                workflow: "code_change_workflow"
              no:
                - question: "Is it a refactor?"
                  yes:
                    category: "refactor"
                    branch_prefix: "refactor/"
                    beads_type: "task"
                    changelog_section: "Changed"
                    workflow: "code_change_workflow"
                  no:
                    - question: "Is it a performance improvement?"
                      yes:
                        category: "perf"
                        branch_prefix: "perf/"
                        beads_type: "task"
                        changelog_section: "Performance"
                        workflow: "code_change_workflow"
                      no:
                        category: "chore"
                        branch_prefix: "chore/"
                        beads_type: "task"
                        changelog_section: null
                        workflow: "code_change_workflow"
      no:
        - question: "Is it a documentation update?"
          yes:
            category: "docs"
            branch_prefix: "docs/"
            beads_type: "task"
            changelog_section: "Documentation"
            workflow: "documentation_workflow"
          no:
            - question: "Is it a question or exploration?"
              yes:
                category: "exploration"
                workflow: "research_workflow"
              no:
                category: "other"
                action: "ask_clarifying_questions"
```

### 1.2 Documentation Update Trigger Tree

```yaml
documentation_triggers:
  input: code_change

  decisions:
    - question: "Does change affect public API?"
      yes:
        update:
          - "README.md (API Reference section)"
          - "docs/api-reference.md"
          - "CHANGELOG.md"

    - question: "Does change affect architecture?"
      yes:
        update:
          - "docs/architecture.md"
          - "CHANGELOG.md"
          - "README.md (Architecture section)"

    - question: "Does change affect performance characteristics?"
      yes:
        update:
          - "README.md (Performance section)"
          - "docs/architecture.md (Performance Architecture)"
          - "CHANGELOG.md (Performance Metrics)"

    - question: "Does change add/modify constraint types?"
      yes:
        update:
          - "README.md (Constraint Hierarchy)"
          - "docs/architecture.md (Constraint System)"
          - "CLAUDE.md (Constraint Development)"
          - "CHANGELOG.md"

    - question: "Does change add/modify language indexer?"
      yes:
        update:
          - "README.md (Supported Languages)"
          - "docs/architecture.md (Indexer Framework)"
          - "CLAUDE.md (Indexer Guidelines)"
          - "CHANGELOG.md"

    - question: "Does change add/modify provider adapter?"
      yes:
        update:
          - "README.md (Provider Support)"
          - "docs/architecture.md (Provider Adapters)"
          - "CHANGELOG.md"

    - question: "Does change add new integration point?"
      yes:
        update:
          - "README.md (Integrations)"
          - "docs/architecture.md (Integration Architecture)"
          - "CLAUDE.md (Integration Guidelines)"
          - "CHANGELOG.md"

    - question: "Does change affect development workflow?"
      yes:
        update:
          - "CONTRIBUTING.md"
          - "CLAUDE.md"
          - "CHANGELOG.md"

    - question: "Does change affect testing requirements?"
      yes:
        update:
          - "CONTRIBUTING.md (Testing Requirements)"
          - "CLAUDE.md (Testing Protocols)"
          - "CHANGELOG.md"
```

### 1.3 Release Decision Tree

```yaml
release_decision:
  input: changelog_unreleased_section

  decisions:
    - question: "Are there breaking changes?"
      yes:
        version_bump: "MAJOR"
        release_type: "major"
        notes_emphasis: "BREAKING CHANGES"
        migration_guide_required: true
      no:
        - question: "Are there new features?"
          yes:
            version_bump: "MINOR"
            release_type: "minor"
            notes_emphasis: "New Features"
            migration_guide_required: false
          no:
            - question: "Are there bug fixes or patches?"
              yes:
                version_bump: "PATCH"
                release_type: "patch"
                notes_emphasis: "Bug Fixes"
                migration_guide_required: false
              no:
                action: "no_release_needed"

    - question: "Does release complete a planned phase?"
      yes:
        phase_milestone: true
        beads_action: "close_phase_epic"
        celebration: "update_performance_table"

    - question: "Does release meet all quality gates?"
      checks:
        - "All tests passing"
        - "Performance benchmarks met"
        - "Documentation updated"
        - "CHANGELOG.md complete"
        - "Migration guide written (if breaking)"
      all_pass:
        proceed: "create_release"
      any_fail:
        action: "block_release_until_fixed"
```

### 1.4 Repository Organization Tree

```yaml
repository_organization:
  input: file_change_or_addition

  decisions:
    - question: "Is this a new file?"
      yes:
        - question: "What type of file?"
          options:
            source_code:
              - question: "Core type system?"
                yes: "src/maze/core/"
              - question: "Constraint abstractions?"
                yes: "src/maze/core/"
              - question: "Indexer (base or language-specific)?"
                yes:
                  - base: "src/maze/indexer/"
                  - language: "src/maze/indexer/languages/"
              - question: "Type system (base or language-specific)?"
                yes:
                  - base: "src/maze/type_system/"
                  - language: "src/maze/type_system/languages/"
              - question: "Synthesis (grammars or templates)?"
                yes:
                  - grammars: "src/maze/synthesis/grammars/"
                  - templates: "src/maze/synthesis/templates/"
              - question: "Orchestrator (base or provider)?"
                yes:
                  - base: "src/maze/orchestrator/"
                  - provider: "src/maze/orchestrator/providers/"
              - question: "Validation?"
                yes: "src/maze/validation/"
              - question: "Repair?"
                yes: "src/maze/repair/"
              - question: "Integration (llguidance, mnemosyne, etc)?"
                yes: "src/maze/integrations/{system_name}/"
              - question: "Public API?"
                yes: "src/maze/api/"
              - question: "Utilities?"
                yes: "src/maze/utils/"

            tests:
              - question: "Unit tests?"
                yes: "tests/unit/{module_name}/"
              - question: "Integration tests?"
                yes: "tests/integration/"
              - question: "End-to-end tests?"
                yes: "tests/e2e/"
              - question: "Performance benchmarks?"
                yes: "benchmarks/"

            documentation:
              - question: "Architecture docs?"
                yes: "docs/"
              - question: "User-facing guide?"
                yes: "README.md or docs/"
              - question: "Developer guide?"
                yes: "CLAUDE.md or CONTRIBUTING.md"
              - question: "Agent guide?"
                yes: "AGENT_GUIDE.md"

            configuration:
              - question: "Project config?"
                yes: "pyproject.toml"
              - question: "CI/CD?"
                yes: ".github/"
              - question: "Git ignore?"
                yes: ".gitignore"

            specs:
              - question: "Original specs/proposals?"
                yes: "specs/origin/"
              - question: "Active specs?"
                yes: "specs/"

    - question: "Is file in wrong location?"
      yes:
        action: "use_git_mv_workflow"
        preserve: "all_references_and_history"

    - question: "Should __init__.py exist?"
      check:
        - "Is this a Python package directory?"
        - "Does directory contain .py files?"
      yes:
        action: "create_init_if_missing"
```

---

## 2. Workflows

### 2.1 Code Change Workflow

**Trigger**: Any code modification (feature, fix, refactor, perf)

**Checklist**:
```
[ ] 1. Classify task using Task Classification Tree
[ ] 2. Create/update Beads issue with correct type
[ ] 3. Create feature branch: {prefix}/{descriptive-name}
[ ] 4. Update Beads issue status to "in_progress"
[ ] 5. Follow Work Plan Protocol (CLAUDE.md §1)
       [ ] Phase 1: Prompt → Spec
       [ ] Phase 2: Spec → Full Spec
       [ ] Phase 3: Full Spec → Plan
       [ ] Phase 4: Plan → Artifacts
[ ] 6. Implement code changes
[ ] 7. Write/update tests (MANDATORY)
       [ ] Unit tests for new code
       [ ] Integration tests if crossing boundaries
       [ ] Performance benchmarks if constraint-related
[ ] 8. Run quality checks:
       [ ] uv run black src/ tests/
       [ ] uv run ruff src/ tests/
       [ ] uv run mypy src/
[ ] 9. Commit changes (BEFORE testing)
       [ ] Use conventional commit format
       [ ] Include performance metrics if applicable
[ ] 10. Run tests (AFTER commit)
       [ ] pkill -f "test"
       [ ] uv run pytest tests/unit -v
       [ ] uv run pytest -m performance -v (if applicable)
[ ] 11. Update documentation (use Doc Update Trigger Tree)
       [ ] Identify affected docs
       [ ] Update each doc comprehensively
       [ ] Update CHANGELOG.md
[ ] 12. Create traceability entry (if new requirement)
[ ] 13. Commit documentation updates
[ ] 14. Push branch and create PR
[ ] 15. Update Beads issue with PR link
[ ] 16. After merge: Close Beads issue with "Complete"
[ ] 17. Delete feature branch
[ ] 18. Store learnings in mnemosyne
```

**Exit Criteria**:
- All quality gates passed
- Tests passing (coverage targets met)
- Documentation updated
- Beads issue closed
- mnemosyne updated with insights

---

### 2.2 Documentation Update Workflow

**Trigger**: Significant change to code, architecture, or processes

**Checklist**:
```
[ ] 1. Use Documentation Update Trigger Tree to identify docs
[ ] 2. For each identified document:

       README.md updates:
       [ ] Quick Start (if API changed)
       [ ] Examples (if usage changed)
       [ ] Performance Metrics (if benchmarks changed)
       [ ] Architecture Overview (if structure changed)
       [ ] Supported Languages (if indexer added)
       [ ] Provider Support (if adapter added)
       [ ] Installation (if dependencies changed)

       CLAUDE.md updates:
       [ ] Work Plan Protocol (if phases changed)
       [ ] Performance-First Protocol (if targets changed)
       [ ] Integration Guidelines (if integrations changed)
       [ ] Constraint Development (if patterns changed)
       [ ] Indexer Guidelines (if languages added)
       [ ] Testing Protocols (if requirements changed)
       [ ] Anti-Patterns (if new violations identified)

       CONTRIBUTING.md updates:
       [ ] Development Workflow (if process changed)
       [ ] Code Standards (if tooling changed)
       [ ] Testing Requirements (if coverage targets changed)
       [ ] Performance Validation (if benchmarks changed)
       [ ] Integration Guidelines (if external systems changed)

       docs/architecture.md updates:
       [ ] Core Components (if structure changed)
       [ ] Constraint System (if hierarchy changed)
       [ ] LLGuidance Integration (if caching changed)
       [ ] Indexer Framework (if languages added)
       [ ] Performance Architecture (if optimizations changed)
       [ ] Extensibility Points (if new extension added)

       CHANGELOG.md updates:
       [ ] Add entry under [Unreleased]
       [ ] Use correct section (Added/Changed/Fixed/etc)
       [ ] Include performance metrics if applicable
       [ ] Reference issue IDs

       AGENT_GUIDE.md updates:
       [ ] Decision Trees (if new decision points)
       [ ] Workflows (if process changed)
       [ ] Templates (if formats changed)
       [ ] Common Scenarios (if new patterns)

[ ] 3. Verify cross-references are consistent
[ ] 4. Check for broken links or outdated sections
[ ] 5. Update table of contents if structure changed
[ ] 6. Commit with descriptive message
[ ] 7. Include in PR or separate docs PR
```

**Exit Criteria**:
- All affected docs updated
- Cross-references consistent
- No broken links
- Changes committed

---

### 2.3 Release Management Workflow

**Trigger**: Unreleased changes ready for versioned release

**Checklist**:
```
[ ] 1. Review CHANGELOG.md [Unreleased] section
[ ] 2. Use Release Decision Tree to determine version bump
[ ] 3. Verify all quality gates:
       [ ] All tests passing (uv run pytest)
       [ ] Performance benchmarks met (pytest -m performance)
       [ ] Coverage targets achieved
       [ ] Documentation complete and updated
       [ ] No TODO/FIXME comments (Beads issues instead)
       [ ] Type checking passes (mypy)
[ ] 4. If breaking changes:
       [ ] Write migration guide in CHANGELOG.md
       [ ] Update CONTRIBUTING.md with upgrade steps
       [ ] Highlight breaking changes in release notes
[ ] 5. Update version in pyproject.toml
[ ] 6. Update CHANGELOG.md:
       [ ] Change [Unreleased] to [X.Y.Z] - YYYY-MM-DD
       [ ] Add new empty [Unreleased] section
       [ ] Ensure all sections populated (Added/Changed/Fixed/etc)
[ ] 7. If phase milestone:
       [ ] Update performance metrics table
       [ ] Close phase epic in Beads
       [ ] Update README.md with phase completion
[ ] 8. Commit release changes:
       git add CHANGELOG.md pyproject.toml
       git commit -m "chore: Release vX.Y.Z"
[ ] 9. Create git tag:
       git tag -a vX.Y.Z -m "Release vX.Y.Z: {brief summary}"
[ ] 10. Push with tags:
       git push origin main --tags
[ ] 11. Create GitHub release:
       gh release create vX.Y.Z \
         --title "vX.Y.Z - {Release Name}" \
         --notes-file <(sed -n '/## \[X.Y.Z\]/,/## \[/p' CHANGELOG.md | head -n -1)
[ ] 12. Verify release:
       [ ] GitHub release page created
       [ ] Tag visible in repository
       [ ] Changelog rendered correctly
[ ] 13. Announce (if major/minor):
       [ ] Update project README.md badges
       [ ] Notify stakeholders
[ ] 14. Store release insights in mnemosyne:
       mnemosyne remember -c "Released vX.Y.Z: {key achievements}" \
         -n "project:maze" -i 9 -t "release,milestone"
```

**Exit Criteria**:
- Version updated in pyproject.toml
- CHANGELOG.md updated with version and date
- Git tag created and pushed
- GitHub release created
- mnemosyne updated

---

### 2.4 Repository Tidying Workflow

**Trigger**: Files in suboptimal locations, missing __init__.py, or organizational debt

**Checklist**:
```
[ ] 1. Identify organizational issues:
       [ ] Files in wrong directories
       [ ] Missing __init__.py in package directories
       [ ] Inconsistent naming conventions
       [ ] Orphaned files (no references)
       [ ] Duplicate functionality

[ ] 2. Plan non-destructive moves:
       [ ] List all files to move
       [ ] Identify all references (imports, docs, tests)
       [ ] Plan move sequence to avoid breaking references
       [ ] Use git mv (NEVER mv or cp)

[ ] 3. For each file move:
       # Example: Moving indexer file
       [ ] git mv src/maze/indexer.py src/maze/indexer/base.py
       [ ] Update all imports:
           # Old: from maze.indexer import BaseIndexer
           # New: from maze.indexer.base import BaseIndexer
       [ ] Update test imports
       [ ] Update documentation references
       [ ] Search for string references in docs:
           grep -r "maze/indexer.py" docs/
       [ ] Update any found references

[ ] 4. For missing __init__.py:
       [ ] Identify Python package directories
       [ ] Create __init__.py with appropriate exports:
           # src/maze/indexer/__init__.py
           from maze.indexer.base import BaseIndexer
           __all__ = ["BaseIndexer"]
       [ ] Verify imports still work

[ ] 5. Verify changes:
       [ ] uv run python -c "import maze; print('OK')"
       [ ] uv run pytest tests/unit -v
       [ ] grep -r "old/path" . (should find nothing)

[ ] 6. Commit with clear message:
       git commit -m "refactor: Reorganize indexer module structure

       - Move indexer.py to indexer/base.py
       - Add indexer/__init__.py with exports
       - Update all imports and references
       - Preserve git history with git mv"

[ ] 7. Update affected documentation:
       [ ] docs/architecture.md (file paths)
       [ ] CONTRIBUTING.md (import examples)
       [ ] README.md (code examples)

[ ] 8. Store organizational insight:
       mnemosyne remember -c "Reorganized indexer: base.py in indexer/ subpackage" \
         -n "project:maze" -i 7 -t "refactor,organization"
```

**Non-Destructive Principles**:
- ALWAYS use `git mv` (preserves history)
- NEVER use `mv` or `cp` (breaks history)
- Update ALL references before committing
- Test imports after each move
- Document reasoning in commit message

**Exit Criteria**:
- All files in correct locations
- All references updated
- Tests passing
- Git history preserved
- Documentation updated

---

### 2.5 Documentation Management

**Trigger**: Documentation updates, architecture changes, or content improvements

#### Structure

```
docs/                     # Markdown source files
├── index.md             # Home page
├── whitepaper.md        # Technical documentation
├── css/styles.css       # Custom design (project-specific colors)
├── js/                  # Theme toggle, sidebar behavior
└── assets/              # Images, diagrams, favicons

templates/               # Jinja2 HTML templates
├── base.html           # Navbar, sidebar, theme toggle
├── index.html          # Home page layout
└── whitepaper.html     # Documentation layout

scripts/build-docs.py   # Python build script
site/                    # Generated static HTML (ignored by git)
```

#### Updating Documentation

1. **Edit markdown files** in `docs/` (index.md, whitepaper.md, etc.)
2. **Test locally** (optional):
   ```bash
   python scripts/build-docs.py
   cd site && python -m http.server 8000
   ```
3. **Commit and push** to main
4. **Verify deployment**: GitHub Actions builds and deploys automatically (~1-2 min)

#### Design System

**Project-specific**:
- **Glyph**: ⊡ (Square) in navbar
- **Colors**: Accent color in `docs/css/styles.css` (`:root` CSS variables)
- **Tagline**: "// Constrained Code Generation" in fixed right sidebar

**Shared features**:
- Geist font + JetBrains Mono for code
- Theme toggle (light/dark)
- Responsive design (sidebar hides <1200px)
- SVG diagrams with light/dark variants

#### Build Process

1. Python-Markdown parses `.md` files
2. YAML front matter stripped automatically
3. Jinja2 templates apply HTML structure
4. Static HTML + CSS/JS copied to `site/`
5. GitHub Actions deploys to GitHub Pages

#### Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check Python dependencies: `pip install markdown jinja2 pygments` |
| Styles missing | Verify `docs/css/styles.css` exists |
| Theme toggle broken | Check `docs/js/theme.js` loaded |
| Diagrams missing | Verify SVG files in `docs/assets/diagrams/` |
| Old content showing | Hard refresh browser (Cmd+Shift+R) |

**Exit Criteria**:
- Documentation files updated
- Local build verified (optional but recommended)
- Changes committed and pushed
- GitHub Actions deployment succeeded
- Live site reflects changes

---

## 3. Templates

### 3.1 Commit Message Template

```
{type}: {brief description (50 chars max)}

{detailed explanation of what and why, not how}

{if performance-related:}
Performance Impact:
- {metric}: {before} → {after}
- {metric}: {before} → {after}

{if breaking change:}
BREAKING CHANGE: {description}
Migration: {how to upgrade}

{if addresses issue:}
Addresses: {beads-issue-id}
```

**Examples**:

```
feat: Add Python indexer with Pyright integration

Implements Python code indexer using Pyright for type analysis
and tree-sitter-python for fast parsing. Extracts functions,
classes, type aliases, and variables with full type annotations.

Performance Impact:
- Indexing speed: 1200 symbols/sec
- Memory usage: 150MB for 10k LOC

Addresses: maze-a2b3
```

```
perf: Optimize grammar caching for TypeScript

Increased LRU cache size from 100k to 200k entries and added
content-based hashing for better cache keys. Reduces mask
computation time for repeated grammar patterns.

Performance Impact:
- p99 latency: 120μs → 45μs
- Cache hit rate: 72% → 89%

Addresses: maze-c4d5
```

```
fix: Prevent race condition in mask cache invalidation

Added mutex lock around cache updates to prevent concurrent
invalidation from multiple threads. Fixes sporadic cache
corruption under high concurrency.

Addresses: maze-e6f7
```

---

### 3.2 Pull Request Template

```markdown
## Summary

{1-3 sentence description of changes}

## Type

- [ ] Feature
- [ ] Fix
- [ ] Refactor
- [ ] Performance
- [ ] Documentation
- [ ] Other: {specify}

## Changes

- {Change 1}
- {Change 2}
- {Change 3}

## Performance Impact (if applicable)

| Metric | Before | After | Target | Status |
|--------|--------|-------|--------|--------|
| {metric} | {value} | {value} | {target} | ✅/⚠️/❌ |

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Performance benchmarks added/updated (if applicable)
- [ ] All tests passing
- [ ] Coverage targets met

## Documentation

- [ ] README.md updated (if public API changed)
- [ ] CLAUDE.md updated (if dev workflow changed)
- [ ] docs/architecture.md updated (if architecture changed)
- [ ] CHANGELOG.md updated
- [ ] Code comments added for complex logic

## Quality Checks

- [ ] Code formatted (black)
- [ ] Linting passed (ruff)
- [ ] Type checking passed (mypy)
- [ ] No TODO/FIXME comments (Beads issues created)
- [ ] Performance targets met (if applicable)

## Beads Issue

Addresses: {beads-issue-id}

## Breaking Changes

{If yes, describe and provide migration guide. If no, write "None"}

## Additional Context

{Any additional context, design decisions, or trade-offs}
```

---

### 3.3 Changelog Entry Template

```markdown
## [Unreleased]

### Added
- {New feature description} ({beads-issue-id})
- {Another new feature} ({beads-issue-id})

### Changed
- {Modified behavior description} ({beads-issue-id})
- {Refactored component} ({beads-issue-id})

### Fixed
- {Bug fix description} ({beads-issue-id})
- {Another bug fix} ({beads-issue-id})

### Performance
- {Optimization description}: {metric before} → {metric after} ({beads-issue-id})

### Documentation
- {Doc update description} ({beads-issue-id})

### Deprecated
- {Deprecated feature with sunset timeline} ({beads-issue-id})

### Removed
- {Removed feature (if breaking)} ({beads-issue-id})

### Security
- {Security fix or improvement} ({beads-issue-id})
```

**Example**:

```markdown
### Added
- Python indexer with Pyright integration (maze-a2b3)
- JSON Schema synthesis from type definitions (maze-b3c4)
- vLLM provider adapter with full CFG support (maze-c4d5)

### Performance
- Grammar caching optimization: p99 120μs → 45μs, cache hit 72% → 89% (maze-d5e6)
- TypeScript indexer parallelization: 1000 → 2500 symbols/sec (maze-e6f7)

### Fixed
- Race condition in mask cache invalidation (maze-f7a8)
- Memory leak in grammar compilation (maze-a8b9)
```

---

### 3.4 Beads Issue Template

```markdown
Title: {Clear, actionable title}

Type: {feature|bug|task|epic}
Priority: {0=critical, 1=high, 2=medium, 3=low}
Assignee: {username or empty}
Labels: {comma-separated tags}

## Description

{Detailed description of work to be done}

## Acceptance Criteria

- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

## Performance Targets (if applicable)

- {Metric}: {target value}
- {Metric}: {target value}

## Dependencies

Blocks: {other-issue-ids}
Blocked by: {other-issue-ids}
Related: {other-issue-ids}

## Implementation Notes

{Technical details, constraints, or suggestions}

## Testing Requirements

- [ ] Unit tests with {coverage}% coverage
- [ ] Integration tests for {scenarios}
- [ ] Performance benchmarks meeting {targets}
- [ ] E2E tests for {workflows}
```

**Example**:

```markdown
Title: Implement Python indexer with Pyright integration

Type: feature
Priority: 1
Labels: indexer, python, phase-2

## Description

Create Python code indexer that extracts symbols, types, and patterns
using Pyright for static analysis and tree-sitter-python for parsing.
Should match TypeScript indexer capabilities and performance.

## Acceptance Criteria

- [ ] Extract functions, classes, type aliases, variables
- [ ] Parse type annotations using Pyright
- [ ] Detect test patterns (pytest, unittest)
- [ ] Extract style conventions
- [ ] Achieve 1000+ symbols/sec indexing speed
- [ ] Memory usage <200MB for 10k LOC

## Performance Targets

- Indexing speed: ≥1000 symbols/sec
- Memory usage: <200MB for 10k LOC
- Type resolution: <100ms per file

## Dependencies

Blocked by: maze-zih.1 (TypeScript indexer must be complete as reference)
Related: maze-zih.2.2 (JSON Schema synthesis needs type info)

## Implementation Notes

- Use Pyright's language server protocol for type analysis
- tree-sitter-python for fast AST parsing
- Follow BaseIndexer interface from indexer/base.py
- Cache type information per-file

## Testing Requirements

- [ ] Unit tests with 80%+ coverage
- [ ] Integration test with Pyright
- [ ] Performance benchmark matching targets
- [ ] Test with real Python codebases (Django, FastAPI examples)
```

---

### 3.5 GitHub Release Notes Template

```markdown
# {Version} - {Release Name}

Released: {YYYY-MM-DD}

## Highlights

{2-3 sentence summary of most important changes}

## What's New

### Added
- {Feature 1 with brief description}
- {Feature 2 with brief description}

### Changed
- {Change 1 with brief description}
- {Change 2 with brief description}

### Fixed
- {Fix 1 with brief description}
- {Fix 2 with brief description}

## Performance

| Metric | Previous | Current | Target | Status |
|--------|----------|---------|--------|--------|
| {metric} | {value} | {value} | {target} | ✅ |
| {metric} | {value} | {value} | {target} | ✅ |

## Breaking Changes

{If any, list with migration guide. If none, write "None in this release."}

## Upgrade Guide

{For MINOR/MAJOR releases}

```bash
# Update dependencies
uv pip install --upgrade maze

# Run migrations (if applicable)
{migration commands}
```

## Contributors

{List of contributors if applicable}

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete details.
```

**Example**:

```markdown
# v0.2.0 - Syntactic Synthesis

Released: 2025-11-15

## Highlights

Phase 2 complete! This release adds comprehensive grammar synthesis
capabilities for all 5 supported languages, JSON Schema generation
from types, and production-ready provider adapters for OpenAI, vLLM,
SGLang, and llama.cpp.

## What's New

### Added
- CFG/Lark grammar builder with language templates (TypeScript, Python, Rust, Go, Zig)
- JSON Schema synthesis from type definitions
- All provider adapters production-ready (OpenAI, vLLM, SGLang, llama.cpp)
- Grammar optimization passes reducing compilation time
- Python indexer with Pyright integration

### Performance

| Metric | Previous | Current | Target | Status |
|--------|----------|---------|--------|--------|
| Mask computation (p99) | 50μs | 48μs | <100μs | ✅ Exceeded |
| Grammar compilation | 42ms | 38ms | <50ms | ✅ Exceeded |
| Cache hit rate | 89% | 91% | >70% | ✅ Exceeded |

## Breaking Changes

None in this release.

## Upgrade Guide

```bash
uv pip install --upgrade maze
```

## Full Changelog

See [CHANGELOG.md](https://github.com/rand/maze/blob/main/CHANGELOG.md#020---2025-11-15) for complete details.
```

---

### 3.6 Mnemosyne Storage Template

```bash
# Architecture decision
mnemosyne remember -c "{Decision and rationale}" \
  -n "project:maze:{component}" -i {8-10} -t "architecture,{tags}" \
  --context "{Additional context}"

# Performance insight
mnemosyne remember -c "{Insight with metrics}" \
  -n "project:maze:{component}" -i {7-9} -t "performance,{tags}"

# Bug root cause
mnemosyne remember -c "{Bug description and root cause}" \
  -n "project:maze:{component}" -i {8-9} -t "bug,gotcha,{tags}"

# Implementation pattern
mnemosyne remember -c "{Pattern and when to use}" \
  -n "project:maze:{component}" -i {7-8} -t "pattern,{tags}"

# Integration lesson
mnemosyne remember -c "{Lesson learned from integration}" \
  -n "project:maze:integrations:{system}" -i {7-9} -t "integration,{tags}"
```

**Examples**:

```bash
# Architecture
mnemosyne remember -c "Using provider adapter pattern for LLM backends allows swapping between OpenAI, vLLM, SGLang without changing orchestrator code" \
  -n "project:maze:orchestrator" -i 9 -t "architecture,patterns,providers" \
  --context "Required for supporting multiple provider capabilities (JSON Schema vs CFG)"

# Performance
mnemosyne remember -c "Grammar compilation caching reduced p99 from 120μs to 45μs by increasing LRU cache from 100k to 200k and using content-based hashing" \
  -n "project:maze:llguidance" -i 8 -t "performance,caching"

# Bug
mnemosyne remember -c "Race condition in mask cache invalidation caused sporadic corruption under high concurrency. Fixed with mutex lock around cache updates" \
  -n "project:maze:llguidance" -i 9 -t "bug,gotcha,concurrency"

# Pattern
mnemosyne remember -c "Use typed holes pattern for cross-component interfaces: define interface early, implement later. Enables parallel development of dependent components" \
  -n "project:maze" -i 8 -t "pattern,workflow,typed-holes"

# Integration
mnemosyne remember -c "mnemosyne recall works best with importance ≥7 for project-specific patterns. Use namespace 'project:maze:component' for scoped recall" \
  -n "project:maze:integrations:mnemosyne" -i 8 -t "integration,memory,patterns"
```

---

## 4. Repository Tidying

### 4.1 Non-Destructive File Movement

**Core Principle**: Preserve git history and all references.

**Process**:

```bash
# 1. Identify file to move
SOURCE="src/maze/old_location/file.py"
TARGET="src/maze/new_location/file.py"

# 2. Find all references BEFORE moving
echo "Finding references to ${SOURCE}..."
grep -r "old_location.file" src/ tests/ docs/
grep -r "old_location/file.py" docs/

# 3. Use git mv (NEVER mv or cp)
git mv "${SOURCE}" "${TARGET}"

# 4. Update imports in code
find src/ tests/ -name "*.py" -exec sed -i '' \
  's/from maze\.old_location\.file/from maze.new_location.file/g' {} \;
find src/ tests/ -name "*.py" -exec sed -i '' \
  's/import maze\.old_location\.file/import maze.new_location.file/g' {} \;

# 5. Update documentation references
find docs/ -name "*.md" -exec sed -i '' \
  's|old_location/file\.py|new_location/file.py|g' {} \;

# 6. Verify no broken references
echo "Checking for remaining old references..."
grep -r "old_location.file" src/ tests/ docs/ && echo "ERROR: References remain!" || echo "OK"

# 7. Test imports
uv run python -c "from maze.new_location.file import SomeClass; print('OK')"

# 8. Run tests
uv run pytest tests/unit -v

# 9. Commit with clear message
git add .
git commit -m "refactor: Move file.py to new_location/

- Relocated from old_location/ to new_location/
- Updated all imports and references
- Preserved git history with git mv
- All tests passing"
```

### 4.2 Adding Missing __init__.py Files

**Process**:

```bash
# 1. Find Python package directories without __init__.py
find src/maze -type d -not -path "*/.*" -exec test ! -e "{}/__init__.py" \; -print

# 2. For each directory, determine what to export
# Example: src/maze/indexer/

# 3. Create __init__.py with appropriate exports
cat > src/maze/indexer/__init__.py << 'EOF'
"""
Maze indexer framework for language-agnostic code analysis.

Provides BaseIndexer interface and language-specific implementations.
"""

from maze.indexer.base import (
    BaseIndexer,
    Symbol,
    IndexingResult,
    ImportInfo,
    TestCase,
    StyleInfo,
)

__all__ = [
    "BaseIndexer",
    "Symbol",
    "IndexingResult",
    "ImportInfo",
    "TestCase",
    "StyleInfo",
]
EOF

# 4. Verify imports work
uv run python -c "from maze.indexer import BaseIndexer; print('OK')"

# 5. Run tests
uv run pytest tests/unit -v

# 6. Commit
git add src/maze/indexer/__init__.py
git commit -m "chore: Add __init__.py to indexer package with exports

- Export BaseIndexer and related types
- Enables clean imports: from maze.indexer import BaseIndexer
- All tests passing"
```

### 4.3 Restructuring Directories

**Scenario**: Moving multiple files to new structure

**Example**: Reorganizing type system

```bash
# Current structure:
# src/maze/types.py  (monolithic)

# Target structure:
# src/maze/type_system/
#   __init__.py
#   base.py
#   context.py
#   inference.py
#   languages/
#     __init__.py
#     typescript.py
#     python.py

# Process:

# 1. Create new directories
mkdir -p src/maze/type_system/languages

# 2. Split monolithic file (manual editing)
# Extract base types → base.py
# Extract context types → context.py
# Extract inference logic → inference.py

# 3. Move/create files with git mv
git mv src/maze/types.py src/maze/type_system/base.py  # If preserving one part
# Create new files for split parts

# 4. Create __init__.py files with exports
cat > src/maze/type_system/__init__.py << 'EOF'
from maze.type_system.base import Type, TypeVariable, TypeParameter
from maze.type_system.context import TypeContext, FunctionSignature
from maze.type_system.inference import infer_type, unify

__all__ = [
    "Type", "TypeVariable", "TypeParameter",
    "TypeContext", "FunctionSignature",
    "infer_type", "unify",
]
EOF

# 5. Update all imports
find src/ tests/ -name "*.py" -exec sed -i '' \
  's/from maze\.types import/from maze.type_system import/g' {} \;

# 6. Verify and test
uv run python -c "from maze.type_system import Type; print('OK')"
uv run pytest tests/unit -v

# 7. Update documentation
# Update all file paths in docs/

# 8. Commit
git add src/maze/type_system/
git commit -m "refactor: Restructure type system into modular package

- Split monolithic types.py into base, context, inference
- Created type_system package with clear structure
- Added languages subpackage for language-specific systems
- Updated all imports and references
- All tests passing"
```

### 4.4 Tidying Checklist

**Regular Maintenance** (before each phase completion):

```
[ ] Check for files in wrong locations
    grep -r "TODO.*move" src/

[ ] Find missing __init__.py files
    find src/maze -type d -not -path "*/.*" -exec test ! -e "{}/__init__.py" \; -print

[ ] Identify orphaned files (no references)
    # For each .py file, check if imported anywhere
    for file in $(find src/maze -name "*.py"); do
        filename=$(basename "$file" .py)
        grep -r "import.*${filename}" src/ tests/ || echo "Orphan: $file"
    done

[ ] Check for inconsistent naming
    # snake_case for modules, PascalCase for classes
    find src/maze -name "*.py" | grep -v "__" | grep "[A-Z]" && echo "Check naming"

[ ] Verify package structure
    # Each directory with .py files should have __init__.py

[ ] Check for duplicate functionality
    # Manual review of similar files

[ ] Update imports to use package exports
    # Use: from maze.indexer import BaseIndexer
    # Not: from maze.indexer.base import BaseIndexer

[ ] Verify git history preserved
    git log --follow <moved-file>

[ ] Run full test suite
    uv run pytest

[ ] Update documentation with new paths

[ ] Commit tidying work
```

---

## 5. Integration Points

### 5.1 Relationship with CLAUDE.md

**CLAUDE.md**: High-level development protocols and principles
**AGENT_GUIDE.md**: Operational workflows and decision trees

**Division**:
- CLAUDE.md defines **WHAT** and **WHY**
  - Work Plan Protocol phases
  - Performance targets and rationale
  - Integration principles
  - Anti-patterns to avoid

- AGENT_GUIDE.md defines **HOW** and **WHEN**
  - Step-by-step workflows
  - Decision trees for task routing
  - Templates for execution
  - Specific commands and sequences

**Cross-References**:
- CLAUDE.md §1 (Work Plan Protocol) → AGENT_GUIDE.md §2.1 (Code Change Workflow)
- CLAUDE.md §2 (Performance-First Protocol) → AGENT_GUIDE.md §6.3 (Performance Optimization Scenario)
- CLAUDE.md §3 (Integration Guidelines) → AGENT_GUIDE.md §2.3 (Release Management includes integration checks)
- CLAUDE.md §8 (Anti-Patterns) → AGENT_GUIDE.md §7 (Anti-Patterns for Agents)

**When to Update Both**:
- New phase added → Update CLAUDE.md principles, AGENT_GUIDE.md workflows
- New quality gate → Update CLAUDE.md targets, AGENT_GUIDE.md checklists
- New integration → Update CLAUDE.md guidelines, AGENT_GUIDE.md templates

### 5.2 Integration with mnemosyne

**Storage Strategy**:

```bash
# At key decision points in workflows:

# During Code Change Workflow (§2.1, step 18)
mnemosyne remember -c "Implemented {feature}: {key insight}" \
  -n "project:maze:{component}" -i 8 -t "implementation,{tags}"

# During Documentation Update (§2.2, step 8)
# (Only for significant architectural changes)
mnemosyne remember -c "Updated architecture: {change and rationale}" \
  -n "project:maze" -i 9 -t "architecture,docs"

# During Release (§2.3, step 14)
mnemosyne remember -c "Released v{version}: {achievements}" \
  -n "project:maze" -i 9 -t "release,milestone"

# During Repository Tidying (§2.4, step 8)
mnemosyne remember -c "Reorganized {component}: {new structure}" \
  -n "project:maze" -i 7 -t "refactor,organization"
```

**Recall Strategy**:

```bash
# Before starting new work
mnemosyne recall -q "{component} implementation patterns" \
  -n "project:maze" -l 5

# When debugging
mnemosyne recall -q "{component} bugs gotchas" \
  --min-importance 8 -l 10

# When integrating
mnemosyne recall -q "integration {external-system}" \
  -n "project:maze:integrations" -l 5

# Cross-project patterns
mnemosyne recall -q "{pattern-name}" --min-importance 7
```

**Importance Levels**:
- 10: Critical architectural decisions (rare)
- 9: Major milestones, releases, breaking changes
- 8: Important implementation patterns, bug root causes
- 7: Performance insights, minor patterns
- 6: General learnings, nice-to-knows

### 5.3 Integration with Beads

**Issue Lifecycle**:

```
1. Discovery (AGENT_GUIDE.md §2.1, step 2)
   └─> bd create "Title" -t {type} -p {priority} --json

2. Planning (CLAUDE.md Phase 3)
   └─> Break into sub-tasks with dot notation
       bd create "Subtask" -t task --id {parent-id}.1

3. Execution (AGENT_GUIDE.md §2.1, step 4)
   └─> bd update {id} --status in_progress --json

4. Documentation (AGENT_GUIDE.md §2.2)
   └─> Updates trigger doc changes (auto-detected)

5. Completion (AGENT_GUIDE.md §2.1, step 16)
   └─> bd close {id} --reason "Complete" --json

6. Release (AGENT_GUIDE.md §2.3)
   └─> Reference in CHANGELOG.md, close epic if phase milestone
```

**Dependencies**:

```bash
# Link discovered work to parent (§2.1)
bd dep add {new-issue} {parent-issue} --type discovered-from

# Block on prerequisites (§2.1, step 2)
bd dep add {current-issue} {blocker-issue} --type blocks

# Visualize (before starting work)
bd dep tree {issue-id}

# Find ready work (unblocked)
bd ready --json --limit 5
```

**Templates** (see §3.4 for full template):
- Use Beads Issue Template for consistency
- Include acceptance criteria, performance targets, dependencies
- Link to CLAUDE.md sections for context

### 5.4 Integration with Git

**Branch Strategy**:

```bash
# Code Change Workflow (§2.1, step 3)
# Format: {type}/{descriptive-name}
git checkout -b feature/python-indexer
git checkout -b fix/cache-race-condition
git checkout -b refactor/type-system-structure
git checkout -b perf/grammar-caching
git checkout -b docs/api-reference-update
```

**Commit Strategy**:

```bash
# Code Change Workflow (§2.1, step 9)
# ALWAYS commit BEFORE testing
git add {changed-files}
git commit -m "{conventional commit message}"  # See §3.1
git log -1 --oneline  # Verify commit

# Then test (§2.1, step 10)
uv run pytest
```

**Release Tagging** (§2.3, step 9):

```bash
# Semantic versioning: vMAJOR.MINOR.PATCH
git tag -a v0.2.0 -m "Release v0.2.0: Syntactic Synthesis complete"
git push origin main --tags
```

**History Preservation** (§4.1):

```bash
# ALWAYS use git mv, NEVER mv
git mv {source} {target}

# Verify history preserved
git log --follow {target}
```

---

### 5.5 llguidance Code Patterns

**Grammar Design**:

```python
# Use Lark extended syntax for CFG grammars
grammar = """
    ?start: typescript_function

    typescript_function: "export"? "async"? "function" IDENT params ret_type block

    params: "(" [param ("," param)*] ")"
    param: IDENT ":" type

    ret_type: ":" type
    type: IDENT | type "[]" | type "|" type | "Promise" "<" type ">"

    block: "{" statement* "}"

    IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/

    %ignore /\\s+/
    %ignore /\\/\\/[^\\n]*/
"""
```

**Mask Computation with Caching**:

```python
from maze.integrations.llguidance import LLGuidanceAdapter

# Initialize with caching enabled
adapter = LLGuidanceAdapter(
    mask_cache_size=100000,  # Large cache for performance
    enable_profiling=True     # Track metrics
)

# Build parser from grammar
parser = adapter.build_parser(grammar)

# Compute masks (automatically cached)
mask = adapter.compute_mask(parser, current_state)

# Check performance
stats = adapter.get_performance_summary()
assert stats['cache_hit_rate'] > 0.7  # Must exceed 70%
assert stats['p99_us'] < 100          # Must be under 100μs
```

**Provider Adapter Pattern**:

```python
from maze.integrations.llguidance import create_adapter

# OpenAI (JSON Schema only)
openai_adapter = create_adapter("openai")
schema = openai_adapter.to_structured_output_schema(grammar)

# vLLM (Full CFG support)
vllm_adapter = create_adapter("vllm")
config = vllm_adapter.to_vllm_config(grammar)

# SGLang (Native llguidance)
sglang_adapter = create_adapter("sglang")
constraint = sglang_adapter.to_sglang_constraint(grammar)
```

**Performance Profiling**:

```python
# Enable profiling during development
adapter.enable_profiling = True

# After generation session
summary = adapter.get_performance_summary()
print(f"Mean: {summary['mean_us']:.1f}μs")
print(f"P99: {summary['p99_us']:.1f}μs")
print(f"Cache hit rate: {summary['cache_hit_rate']:.1%}")

# Validate targets (from CLAUDE.md)
assert summary['p99_us'] < 100
assert summary['cache_hit_rate'] > 0.7
```

---

### 5.6 pedantic_raven Integration Patterns

**Semantic Validation**:

```python
from maze.integrations.pedantic_raven import RavenAdapter

raven = RavenAdapter()

# Validate generated code against specification
result = await raven.validate_semantic(
    code=generated_code,
    spec=specification,
    mode="moderate"  # strict, moderate, or lenient
)

if not result.passed:
    # Feed violations back to repair loop
    for violation in result.violations:
        print(f"Property violation: {violation.message}")
        # Use to tighten constraints
```

**Property Specification**:

```python
from maze.core.constraints import SemanticConstraint

# Define behavioral properties
constraint = SemanticConstraint(
    specification="Function must handle empty arrays gracefully"
)

# Add test cases
constraint.add_test_case(
    input=[],
    expected_output=None  # Should not throw
)

# Add properties for validation
constraint.add_property("Returns null for empty input")
constraint.add_invariant("Never throws exception")
```

**Integration Workflow**:
1. Generate code with syntactic/type constraints
2. Validate with pedantic_raven (semantic check)
3. If violations found → tighten constraints
4. Retry generation
5. Store successful patterns in mnemosyne

---

### 5.7 RUNE Execution Patterns

**Sandboxed Test Execution**:

```python
from maze.integrations.rune import RuneAdapter

rune = RuneAdapter()

# Execute tests in isolated sandbox
result = await rune.execute_tests(
    code=generated_code,
    tests=specification.tests,
    timeout=30,           # 30 second limit
    memory_limit_mb=512   # 512MB memory limit
)

# Check results
if result.passed:
    print(f"All {len(result.results)} tests passed")
else:
    failed = [r for r in result.results if not r.success]
    # Feed failures to repair loop
    for test in failed:
        print(f"Test failed: {test.name}")
        print(f"Error: {test.error_message}")
```

**Safety Configuration**:

```python
# Configure sandbox isolation
rune_config = {
    "network_isolation": True,      # No external calls
    "filesystem_isolation": True,   # Temporary sandbox
    "cpu_limit_percent": 80,        # Max 80% CPU
    "memory_limit_mb": 512,         # Max 512MB RAM
    "timeout_seconds": 30,          # Max 30 seconds
    "deterministic": True           # Same input → same output
}

result = await rune.execute_tests(
    code=generated_code,
    tests=tests,
    **rune_config
)
```

**Integration Workflow**:
1. Generate code (syntactic + type + semantic constraints)
2. Run tests in RUNE sandbox (safety guaranteed)
3. Extract diagnostics from test results
4. If failures → analyze and tighten constraints
5. Retry generation
6. Never execute untrusted code outside sandbox

---

## 6. Common Scenarios

### 6.1 Scenario: Adding New Language Indexer

**Context**: User requests support for a new language (e.g., Ruby)

**Workflow**:

```
1. Task Classification (§1.1)
   └─> Category: feature
   └─> Branch: feature/ruby-indexer
   └─> Beads type: feature

2. Create Beads Issue (§3.4)
   └─> bd create "Implement Ruby indexer" -t feature -p 1 \
       --json > issue.json
   └─> Extract ID from JSON

3. Follow Work Plan Protocol (CLAUDE.md §1)
   Phase 1: Research Ruby type systems (Sorbet, RBS)
   Phase 2: Design indexer architecture, typed holes
   Phase 3: Plan implementation sequence
   Phase 4: Implement

4. Code Change Workflow (§2.1)
   [ ] Create feature branch
   [ ] Update Beads to in_progress
   [ ] Implement src/maze/indexer/languages/ruby.py
   [ ] Write tests/unit/test_indexer/test_ruby.py
   [ ] Write performance benchmark
   [ ] Quality checks (black, ruff, mypy)
   [ ] Commit (BEFORE testing)
   [ ] Run tests (AFTER commit)

5. Documentation Update Workflow (§2.2)
   Using Doc Update Trigger Tree (§1.2):
   [ ] README.md: Supported Languages table
   [ ] docs/architecture.md: Indexer Framework table
   [ ] CLAUDE.md: Add Ruby indexer guidelines (§5)
   [ ] CHANGELOG.md: Under [Unreleased] → Added

6. Quality Verification
   [ ] Performance benchmark: ≥1000 symbols/sec
   [ ] Coverage: ≥80%
   [ ] Type checking passes

7. PR and Merge (§3.2)
   [ ] Push branch
   [ ] Create PR with template
   [ ] Reference Beads issue
   [ ] Merge after approval

8. Post-Merge
   [ ] Close Beads issue
   [ ] Store learnings in mnemosyne:
       mnemosyne remember -c "Ruby indexer uses Sorbet for types: {insight}" \
         -n "project:maze:indexer" -i 8 -t "ruby,indexer,implementation"

9. If Phase Milestone
   [ ] Consider release (§2.3)
```

---

### 6.2 Scenario: Performance Optimization

**Context**: Mask computation exceeds 100μs target

**Workflow**:

```
1. Identify Issue
   └─> Performance benchmark fails
   └─> Create Beads bug:
       bd create "Mask computation exceeds 100μs target" \
         -t bug -p 0 --json

2. Investigation
   [ ] Review performance metrics (§8.1)
   [ ] Profile with built-in profiler
   [ ] Identify bottleneck
   [ ] Recall similar issues:
       mnemosyne recall -q "mask computation performance" \
         -n "project:maze:llguidance" -l 10

3. Optimization (Code Change Workflow §2.1)
   Branch: perf/mask-computation-caching
   [ ] Implement optimization
   [ ] Run benchmark to verify improvement
   [ ] Commit with metrics:
       "perf: Optimize mask caching

       Performance Impact:
       - p99: 150μs → 45μs
       - Cache hit rate: 65% → 89%"

4. Documentation (§2.2)
   [ ] README.md: Update performance metrics table
   [ ] docs/architecture.md: Update Performance Architecture
   [ ] CHANGELOG.md: Add under Performance section

5. Verification
   [ ] uv run pytest -m performance -v
   [ ] All benchmarks pass
   [ ] p99 < 100μs ✅

6. Knowledge Capture
   mnemosyne remember -c "Mask cache optimization: increased LRU from 100k to 200k, content-based hashing. p99: 150μs → 45μs" \
     -n "project:maze:llguidance" -i 8 -t "performance,caching,optimization"

7. Close Issue
   bd close {issue-id} --reason "Complete" --json
```

---

### 6.3 Scenario: Phase Milestone Release

**Context**: Phase 2 complete, ready for v0.2.0 release

**Workflow**:

```
1. Pre-Release Verification
   [ ] All Phase 2 Beads issues closed
   [ ] All tests passing: uv run pytest
   [ ] Performance benchmarks met: pytest -m performance
   [ ] Coverage targets achieved
   [ ] Documentation complete

2. Review CHANGELOG.md [Unreleased]
   [ ] All changes documented
   [ ] Sections: Added, Changed, Fixed, Performance
   [ ] Issue IDs referenced

3. Release Decision (§1.3)
   └─> New features? Yes → MINOR bump
   └─> Breaking changes? No
   └─> Version: 0.1.0 → 0.2.0

4. Release Management Workflow (§2.3)
   [ ] Update pyproject.toml: version = "0.2.0"
   [ ] Update CHANGELOG.md:
       - [Unreleased] → [0.2.0] - 2025-11-15
       - Add new [Unreleased] section
   [ ] Update README.md performance table if exceeded targets
   [ ] Commit: git commit -m "chore: Release v0.2.0"
   [ ] Tag: git tag -a v0.2.0 -m "Release v0.2.0: Syntactic Synthesis"
   [ ] Push: git push origin main --tags

5. Create GitHub Release (§3.5)
   gh release create v0.2.0 \
     --title "v0.2.0 - Syntactic Synthesis" \
     --notes-file <(sed -n '/## \[0.2.0\]/,/## \[/p' CHANGELOG.md | head -n -1)

6. Close Phase Epic
   bd close maze-zih.2 --reason "Complete - Phase 2 milestone achieved" --json

7. Store Milestone
   mnemosyne remember -c "Released v0.2.0: Grammar synthesis for 5 languages, JSON Schema generation, all provider adapters production-ready. All performance targets exceeded." \
     -n "project:maze" -i 10 -t "release,milestone,phase-2"

8. Announce
   [ ] Update README.md badges if applicable
   [ ] Notify stakeholders
```

---

### 6.4 Scenario: Bug Fix with Urgency

**Context**: Critical bug in production affecting users

**Workflow**:

```
1. Immediate Triage
   └─> Create Beads issue:
       bd create "Critical: {brief description}" \
         -t bug -p 0 --json

2. Fast-Track (Condensed Work Plan)
   Phase 1: Understand bug (minimal spec)
   Phase 2: Plan fix (typed hole if needed)
   Phase 3: Quick plan
   Phase 4: Fix and verify

3. Branch and Fix
   git checkout -b fix/{descriptive-name}
   bd update {issue-id} --status in_progress --json

   [ ] Implement minimal fix
   [ ] Write regression test
   [ ] Verify fix: uv run pytest

4. Commit and Test
   git commit -m "fix: {description}

   Root cause: {brief explanation}
   Addresses: {issue-id}"

   uv run pytest tests/unit -v

5. Emergency Documentation
   [ ] CHANGELOG.md: Add under Fixed
   [ ] Add comment in code explaining fix
   [ ] Skip extensive docs (document in follow-up)

6. Fast PR
   git push -u origin fix/{name}
   gh pr create --title "Critical Fix: {description}" \
     --body "Emergency fix for {issue-id}"

7. Post-Merge
   [ ] Close Beads issue
   [ ] Store root cause:
       mnemosyne remember -c "{Bug description and root cause}" \
         -n "project:maze:{component}" -i 9 -t "bug,gotcha,critical"
   [ ] Consider immediate patch release (§2.3)
   [ ] Schedule follow-up for comprehensive docs/tests

8. Follow-Up Issue
   bd create "Comprehensive tests for {bug area}" \
     -t task -p 1 --json
   bd dep add {new-issue} {bug-issue} --type discovered-from
```

---

### 6.5 Scenario: Documentation-Only Update

**Context**: User reports unclear documentation, no code changes

**Workflow**:

```
1. Task Classification (§1.1)
   └─> Category: docs
   └─> Branch: docs/{description}
   └─> Beads type: task

2. Create Issue
   bd create "Clarify {topic} in documentation" \
     -t task -p 2 -l documentation --json

3. Documentation Workflow (§2.2)
   git checkout -b docs/clarify-{topic}
   bd update {issue-id} --status in_progress --json

   [ ] Identify affected docs (§1.2)
   [ ] Update each comprehensively
   [ ] Add examples if missing
   [ ] Check cross-references
   [ ] Verify links work

4. Commit
   git commit -m "docs: Clarify {topic}

   - Added examples for {X}
   - Clarified {Y}
   - Fixed broken link to {Z}

   Addresses: {issue-id}"

5. PR (simplified, docs-only)
   gh pr create --title "docs: Clarify {topic}" \
     --body "Addresses user confusion about {topic}.

     Changes:
     - {change 1}
     - {change 2}"

6. CHANGELOG (optional for minor docs)
   # Only if significant:
   [Unreleased]
   ### Documentation
   - Clarified {topic} with examples ({issue-id})

7. Close
   bd close {issue-id} --reason "Complete" --json
```

---

### 6.6 Scenario: Refactoring Without Behavior Change

**Context**: Code needs restructuring for maintainability

**Workflow**:

```
1. Task Classification
   └─> Category: refactor
   └─> Branch: refactor/{component}
   └─> Beads type: task

2. Create Issue with Rationale
   bd create "Refactor {component} for {reason}" \
     -t task -p 2 --json

   Description: Current structure has {problem}.
   Refactoring will {benefit}.

3. Refactoring Plan (CLAUDE.md Phase 2-3)
   [ ] Identify components to restructure
   [ ] Map dependencies
   [ ] Plan non-destructive moves (§4.1)
   [ ] Ensure tests exist (add if missing)

4. Execute Refactoring
   git checkout -b refactor/{component}

   [ ] Run tests BEFORE: uv run pytest (baseline)
   [ ] Make changes using git mv
   [ ] Update all imports and references (§4.1)
   [ ] Commit incremental changes
   [ ] Run tests AFTER: uv run pytest (verify)
   [ ] Verify no behavior change

5. Documentation
   [ ] Update file paths in docs
   [ ] Update import examples in CONTRIBUTING.md
   [ ] CHANGELOG.md under Changed:
       "Refactored {component}: {new structure}"

6. PR with Clear Rationale
   Title: "refactor: Restructure {component}"
   Body:
   - Before: {old structure}
   - After: {new structure}
   - Rationale: {why this is better}
   - No behavior change (tests confirm)

7. Store Pattern
   mnemosyne remember -c "Refactored {component} to {pattern}: {benefit}" \
     -n "project:maze" -i 7 -t "refactor,pattern"
```

---

### 6.7 Scenario: Adding Integration with External System

**Context**: Integrating new external tool (e.g., new validation system)

**Workflow**:

```
1. Research Phase (Work Plan Phase 1)
   [ ] Study external system API/docs
   [ ] Recall similar integrations:
       mnemosyne recall -q "integration patterns" \
         -n "project:maze:integrations" -l 5
   [ ] Define integration boundary (typed hole)

2. Create Integration Epic
   bd create "Integrate {system}" -t epic -p 1 --json

   Sub-tasks:
   bd create "Design {system} adapter interface" -t task --id {epic}.1
   bd create "Implement {system} client" -t task --id {epic}.2
   bd create "Add integration tests" -t task --id {epic}.3
   bd create "Update documentation" -t task --id {epic}.4

3. Implementation (Code Change Workflow §2.1)
   Branch: feature/integrate-{system}

   [ ] Create src/maze/integrations/{system}/
   [ ] Implement adapter following existing pattern
   [ ] Write unit tests
   [ ] Write integration tests (may need mocks)
   [ ] Performance benchmark if applicable

4. Documentation (§2.2)
   [ ] README.md: Add to Integrations section
   [ ] docs/architecture.md: Integration Architecture
   [ ] CLAUDE.md: Add integration guidelines (§3)
   [ ] AGENT_GUIDE.md: Add to templates if needed (§3)
   [ ] CHANGELOG.md: Under Added

5. Integration Testing
   [ ] Test with actual external system (not just mocks)
   [ ] Document required credentials/setup
   [ ] Add to CI/CD if possible

6. Knowledge Capture
   mnemosyne remember -c "{System} integration: {key patterns and gotchas}" \
     -n "project:maze:integrations:{system}" -i 8 -t "integration,{system}"

   Examples:
   - Authentication approach
   - Rate limiting handling
   - Error scenarios
   - Performance characteristics

7. Close Epic
   bd close {epic-id} --reason "Complete" --json
```

---

### 6.8 Scenario: Dependency Update

**Context**: Upstream dependency releases new version

**Workflow**:

```
1. Assess Impact
   [ ] Review upstream changelog
   [ ] Identify breaking changes
   [ ] Check if update required (security, features, fixes)

2. Create Issue
   bd create "Update {dependency} to v{version}" \
     -t task -p {priority} --json

   Priority:
   - 0 if security fix
   - 1 if blocking feature
   - 2 if nice-to-have

3. Update and Test
   git checkout -b chore/update-{dependency}

   [ ] Update pyproject.toml
   [ ] uv pip install --upgrade {dependency}
   [ ] Run full test suite: uv run pytest
   [ ] Run performance benchmarks: pytest -m performance
   [ ] Check for deprecation warnings

4. Handle Breaking Changes
   If breaking:
   [ ] Update code to new API
   [ ] Add migration notes
   [ ] Update CHANGELOG with BREAKING CHANGE

5. Documentation
   [ ] CHANGELOG.md:
       ### Changed
       - Updated {dependency} from v{old} to v{new} ({issue-id})

       If breaking:
       ### BREAKING CHANGES
       - {Dependency} updated: {migration guide}

   [ ] README.md: Update dependency version if documented

6. Commit and PR
   git commit -m "chore: Update {dependency} to v{version}

   Changes:
   - {change 1}
   - {change 2}

   {If breaking: BREAKING CHANGE: {description}}"

7. Version Bump Decision (§1.3)
   - Breaking dependency change → MAJOR bump
   - New dependency features used → MINOR bump
   - Bug fix dependency → PATCH bump
```

---

### 6.9 Scenario: Repository Cleanup

**Context**: Periodic maintenance to keep repo organized

**Workflow**:

```
1. Create Maintenance Issue
   bd create "Repository maintenance: {date}" \
     -t task -p 3 -l maintenance --json

2. Run Tidying Checklist (§4.4)
   [ ] Check for misplaced files
   [ ] Find missing __init__.py
   [ ] Identify orphaned files
   [ ] Check naming consistency
   [ ] Verify package structure

3. Execute Tidying (§4)
   git checkout -b chore/repo-cleanup-{date}

   For each issue found:
   [ ] Use Repository Tidying Workflow (§2.4)
   [ ] Non-destructive moves only (git mv)
   [ ] Update all references
   [ ] Commit incrementally
   [ ] Test after each change

4. Verify
   [ ] All tests passing
   [ ] All imports working
   [ ] Documentation paths correct
   [ ] Git history preserved

5. Comprehensive Commit
   git commit -m "chore: Repository cleanup {date}

   - Moved {X} to correct location
   - Added missing __init__.py to {Y}
   - Removed orphaned {Z}
   - Updated all references
   - Tests passing"

6. PR with Summary
   Title: "chore: Repository cleanup"
   Body:
   - Organized: {what was reorganized}
   - Added: {what was added}
   - Removed: {what was removed}
   - All references updated, tests passing

7. Close and Store
   bd close {issue-id} --reason "Complete" --json

   mnemosyne remember -c "Repo cleanup {date}: {key changes}" \
     -n "project:maze" -i 6 -t "maintenance,organization"
```

---

### 6.10 Scenario: User Requests Vague Feature

**Context**: User says "make it faster" without specifics

**Workflow**:

```
1. Clarification Phase (CRITICAL)
   Ask specific questions:
   - What operation is slow?
   - What is current performance?
   - What is target performance?
   - Is this measured or perceived?
   - What is use case context?

2. Measurement
   [ ] Identify specific operation
   [ ] Run existing benchmarks
   [ ] Profile if no benchmark exists:
       uv run python -m cProfile -o profile.stats {script}
   [ ] Quantify current performance

3. Define Spec (Work Plan Phase 1)
   Write spec.md:
   - Current: {operation} takes {X}
   - Target: {operation} should take <{Y}
   - Context: {use case}
   - Constraints: {any}

4. Get Approval
   Present to user:
   "Based on profiling, {operation} takes {X}. I'll optimize to <{Y}
   by {approach}. This addresses {use case}. Proceed?"

5. Only After Approval: Implementation
   Follow Performance Optimization Scenario (§6.2)

6. Avoid:
   ❌ Optimizing without measuring
   ❌ Guessing what's slow
   ❌ Proceeding without target
   ❌ Starting without approval
```

---

## 7. Anti-Patterns for Agents

### 7.1 Grammar Design Anti-Patterns

**❌ CRITICAL: Never Use Inline Rules with llguidance**

```lark
# ❌ WRONG - llguidance does NOT support ?start:
?start: function_body
function_body: statement+

# ✅ CORRECT - Use standard start rule
start: function_body
function_body: statement+
```

**Why**: llguidance supports "a variant of Lark syntax" but NOT inline rules (`?rule:`). This will cause "Failed to convert the grammar from GBNF to Lark" errors.

**❌ CRITICAL: Don't Use Full Generation Grammars for Completion**

```python
# ❌ WRONG - Using full function grammar for completion
prompt = "def calculate_sum(a: int, b: int) -> int:"
grammar = PYTHON_FUNCTION  # Starts with "def" IDENT ...
# Result: Signature duplication, invalid code

# ✅ CORRECT - Use completion grammar
prompt = "def calculate_sum(a: int, b: int) -> int:"
grammar = PYTHON_FUNCTION_BODY  # Starts with suite/body only
# Result: Completes body correctly
```

**Why**: Maze's primary use case is **code completion** (completing partial code), not full generation from scratch. The prompt already contains the signature.

**❌ Don't Test Constraints with "assert code is not None"**

```python
# ❌ WRONG - Meaningless test
def test_generation():
    result = generate_with_grammar(prompt, grammar)
    assert result.code is not None  # Doesn't validate constraints!

# ✅ CORRECT - Validate grammar enforcement
def test_generation():
    grammar = "start: simple\nsimple: \"return \" NUMBER\nNUMBER: /[0-9]+/"
    result = generate_with_grammar(prompt, grammar)
    
    # 1. Parse successfully
    ast.parse(result.code)
    
    # 2. Verify it followed grammar
    assert "return" in result.code
    assert any(c.isdigit() for c in result.code)
    
    # 3. Verify it did NOT violate grammar
    assert "#" not in result.code  # Grammar forbids comments
    assert "if" not in result.code  # Grammar forbids conditionals
```

**Why**: The value proposition is that grammars ENFORCE constraints. Tests must validate this.

### 7.2 vLLM API Anti-Patterns

**❌ Don't Use Deprecated guided_grammar Parameter**

```python
# ❌ WRONG - Old vLLM 0.8.x API
sampling_params = SamplingParams(
    guided_grammar=grammar,  # DEPRECATED
)

# ✅ CORRECT - vLLM 0.11.0+ V1 API
from vllm.sampling_params import StructuredOutputsParams

sampling_params = SamplingParams(
    structured_outputs=StructuredOutputsParams(grammar=grammar),
)
```

**Why**: vLLM V1 engine (default in 0.11.0+) uses new API. Old API is deprecated.

**❌ Don't Forget to Set Backend to "guidance"**

```python
# ❌ WRONG - No backend specified
llm = LLM(model="Qwen/Qwen2.5-Coder-32B-Instruct")

# ✅ CORRECT - Enable llguidance backend
llm = LLM(
    model="Qwen/Qwen2.5-Coder-32B-Instruct",
    structured_outputs_config={"backend": "guidance"},
)
```

**Why**: vLLM V1 supports multiple backends (guidance, outlines, lm-format-enforcer). Must explicitly set to "guidance" for Lark grammar support.

### 7.3 Testing Anti-Patterns

**❌ Don't Test Only with Mocks**

```python
# ❌ WRONG - Mock hides real issues
def test_with_mock():
    mock_llm = Mock()
    mock_llm.generate.return_value = "return 42"
    # Passes but doesn't validate actual grammar enforcement

# ✅ CORRECT - Test with real Modal endpoint
def test_with_modal():
    adapter = ModalProviderAdapter()
    result = adapter.generate(request_with_grammar)
    # Actually validates llguidance works
```

**Why**: Mocks don't reveal:
- Grammar syntax issues (`?start:` incompatibility)
- Token limit edge cases
- Temperature effects on constraint following
- Actual llguidance behavior

**❌ Don't Ignore Cold Start Times**

```python
# ❌ WRONG - Timeout too short for cold start
response = requests.post(endpoint, json=payload, timeout=30)

# ✅ CORRECT - Allow time for model loading
response = requests.post(endpoint, json=payload, timeout=120)
```

**Why**: Modal has cold starts (60-120s) when loading 32B models. First request will timeout with <120s timeout.

## 7. Anti-Patterns for Agents (Original Section)

### 7.1 Work Plan Violations

```
❌ Skip Phase 1 (spec) and jump to coding
   → Result: Implement wrong thing, rework later
   → Fix: Always clarify requirements first

❌ Skip Phase 2 (decomposition) for "quick tasks"
   → Result: Miss dependencies, break things
   → Fix: Even small tasks need typed holes

❌ Proceed without exit criteria met
   → Result: Incomplete work, technical debt
   → Fix: Verify each phase complete before proceeding

❌ Skip Phase 3 (planning) and write unordered code
   → Result: Blocked by missing dependencies
   → Fix: Sequence tasks by dependencies
```

### 7.2 Testing Violations

```
❌ Test before committing
   → Result: Test stale code, invalid results
   → Fix: ALWAYS commit first, then test

❌ Test while changing code
   → Result: Tests run against unknown state
   → Fix: Commit, THEN test, THEN change

❌ Skip tests "just this once"
   → Result: Bugs in production
   → Fix: Tests are MANDATORY, no exceptions

❌ Skip performance benchmarks for constraints
   → Result: Miss performance regressions
   → Fix: Performance benchmarks required for all constraint work

❌ Mock external systems in integration tests
   → Result: Integration issues in production
   → Fix: Test with actual systems when possible
```

### 7.3 Documentation Violations

```
❌ Update code without updating docs
   → Result: Docs become stale, users confused
   → Fix: Use Documentation Update Trigger Tree (§1.2)

❌ Update only one doc when many affected
   → Result: Inconsistent documentation
   → Fix: Check ALL docs for each change

❌ Skip CHANGELOG.md entries
   → Result: Changes invisible to users
   → Fix: EVERY user-facing change goes in CHANGELOG

❌ Write vague changelog entries
   → Bad: "Fixed bug"
   → Good: "Fixed race condition in mask cache invalidation ({issue-id})"

❌ Forget to update API reference when API changes
   → Result: Wrong examples in docs
   → Fix: API change ALWAYS triggers doc update
```

### 7.4 Repository Organization Violations

```
❌ Use mv instead of git mv
   → Result: Git history lost
   → Fix: ALWAYS use git mv

❌ Move file without updating references
   → Result: Broken imports
   → Fix: Update ALL references before committing (§4.1)

❌ Create files in wrong locations
   → Result: Organizational debt
   → Fix: Use Repository Organization Tree (§1.4)

❌ Forget __init__.py in package directories
   → Result: Import errors
   → Fix: Check for __init__.py after creating directories

❌ Leave orphaned files after refactoring
   → Result: Confusion about canonical implementation
   → Fix: Remove old files, update references
```

### 7.5 Git Workflow Violations

```
❌ Commit to main directly
   → Result: Bypass PR review, quality gates
   → Fix: ALWAYS use feature branches

❌ Vague commit messages
   → Bad: "changes", "wip", "fixed"
   → Good: Use conventional commits template (§3.1)

❌ Forget to push tags after release
   → Result: GitHub release missing
   → Fix: git push origin main --tags (§2.3, step 10)

❌ Amend commits after push
   → Result: Rewrite public history, confuse collaborators
   → Fix: Only amend local unpushed commits

❌ Force push to main
   → Result: Destroy team's work
   → Fix: NEVER force push to main
```

### 7.6 Beads Integration Violations

```
❌ Start work without creating Beads issue
   → Result: Work not tracked
   → Fix: Create issue first (§2.1, step 2)

❌ Forget to update issue status
   → Result: Stale state, confusing tracking
   → Fix: Update status at each transition

❌ Close issue before work complete
   → Result: False completion signals
   → Fix: Only close after all acceptance criteria met

❌ Skip dependency links
   → Result: Miss blocking issues
   → Fix: Link dependencies (§5.3)

❌ Generic issue titles
   → Bad: "Fix bug"
   → Good: "Fix race condition in mask cache invalidation"
```

### 7.7 mnemosyne Integration Violations

```
❌ Forget to store critical decisions
   → Result: Lose reasoning, repeat mistakes
   → Fix: Store at key decision points (§5.2)

❌ Store everything (noise)
   → Result: Dilute important memories
   → Fix: Use importance levels correctly (8-10 for critical)

❌ Vague memory content
   → Bad: "Optimized code"
   → Good: "Mask cache optimization: LRU 100k→200k, content hashing. p99: 150μs→45μs"

❌ Wrong namespace
   → Result: Recall misses relevant memories
   → Fix: Use project:maze:{component} structure

❌ Skip context field
   → Result: Lose nuance and reasoning
   → Fix: Add context for important memories
```

### 7.8 Performance Violations

```
❌ Optimize without measuring
   → Result: Waste time on non-bottlenecks
   → Fix: Profile first, optimize second

❌ Miss performance targets without raising
   → Result: Performance debt accumulates
   → Fix: Fail loudly when targets missed

❌ Skip performance docs update
   → Result: Stale metrics in README
   → Fix: Update performance tables (§2.2)

❌ Break performance without notice
   → Result: Regressions slip through
   → Fix: Run performance benchmarks in CI
```

### 7.9 Integration Violations

```
❌ Bypass llguidance for "simple" constraints
   → Result: Inconsistent constraint enforcement
   → Fix: ALL constraints go through llguidance

❌ Hard-code mnemosyne namespaces
   → Result: Namespace conflicts
   → Fix: Use project:maze:{component} pattern

❌ Skip RUNE sandbox for "trusted" code
   → Result: Security vulnerabilities
   → Fix: ALL generated code runs in sandbox

❌ Mock pedantic_raven in production
   → Result: Skip semantic validation
   → Fix: Real integration tests
```

### 7.10 Release Violations

```
❌ Release without updating version
   → Result: Version mismatch
   → Fix: Update pyproject.toml (§2.3, step 5)

❌ Release without git tag
   → Result: No version marker in history
   → Fix: Create annotated tag (§2.3, step 9)

❌ Release with failing tests
   → Result: Broken release
   → Fix: Verify all quality gates (§2.3, step 3)

❌ Skip migration guide for breaking changes
   → Result: Users can't upgrade
   → Fix: Write migration guide (§2.3, step 4)

❌ Forget to close phase epic
   → Result: Beads state stale
   → Fix: Close epic at milestones (§2.3, step 14)
```

---

## 8. Observability

### 8.1 Performance Metrics Tracking

**Location**: Performance metrics embedded in code via profiling

**How to Check**:

```python
# In llguidance adapter
adapter = LLGuidanceAdapter(enable_profiling=True)

# After operations
stats = adapter.get_performance_summary()
print(f"p99: {stats['p99_us']:.1f}μs")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")

# Assert targets in tests
assert stats['p99_us'] < 100, f"p99 {stats['p99_us']:.1f}μs exceeds target"
```

**Monitoring During Development**:

```bash
# Run performance benchmarks
uv run pytest -m performance -v

# Output shows:
# - p99 latency (target: <100μs)
# - Cache hit rate (target: >70%)
# - Memory usage (target: <1GB)

# Check for regressions
uv run python benchmarks/mask_computation.py
```

**Updating Performance Docs** (when metrics improve):

```markdown
# README.md

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Token mask (p99) | <100μs | 45μs | ✅ Exceeded |
| Cache hit rate | >70% | 91% | ✅ Exceeded |
```

### 8.2 Test Coverage Monitoring

**Check Coverage**:

```bash
# Run with coverage
uv run pytest --cov=src/maze --cov-report=term-missing tests/unit

# Output shows:
# - Overall coverage %
# - Per-module coverage
# - Missing lines

# HTML report for details
uv run pytest --cov=src/maze --cov-report=html tests/unit
open htmlcov/index.html
```

**Coverage Targets** (from CONTRIBUTING.md):

```
Core type system: 90%+
Constraint synthesis: 85%+
Indexers: 80%+ per language
LLGuidance adapter: 85%+
Overall: 70%+
```

**CI/CD Integration** (future):

```yaml
# .github/workflows/test.yml
- name: Check coverage
  run: |
    uv run pytest --cov=src/maze --cov-report=term --cov-fail-under=70
```

### 8.3 Beads Issue Tracking

**Check Project Health**:

```bash
# Ready work (unblocked tasks)
bd ready --json | jq 'length'
# → Should be >0 but <10 (work available, not overwhelming)

# Open issues by type
bd list --status open --type feature --json | jq 'length'
bd list --status open --type bug --json | jq 'length'

# Critical issues
bd list --status open --priority 0 --json
# → Should be 0 or very few

# In-progress work
bd list --status in_progress --json | jq 'length'
# → Should match active work (1-3 typical)

# Dependency tree health
bd dep tree {epic-id}
# → Visualize blocked/blocking relationships
```

**Phase Progress**:

```bash
# Check phase epic completion
bd show maze-zih.2  # Phase 2 epic

# Check sub-task completion
bd list --status closed --json | grep "maze-zih.2\."
# → Count completed sub-tasks
```

**Cleanup Indicators**:

```bash
# Stale in-progress issues (stuck?)
bd list --status in_progress --json | jq '.[] | select(.updated_at < "2025-11-01")'

# Unassigned critical bugs
bd list --type bug --priority 0 --no-assignee --json
# → Should be 0
```

### 8.4 Documentation Consistency

**Check for Staleness**:

```bash
# Files changed since last doc update
git log --since="2 weeks ago" --name-only --pretty=format: | sort -u | grep "^src/"

# Cross-reference with doc update dates
ls -lt docs/ README.md CLAUDE.md CHANGELOG.md | head -n 5

# If src/ changed recently but docs didn't → investigate
```

**Verify Cross-References**:

```bash
# Check for broken internal links
grep -r "\[.*\](.*\.md" docs/ README.md CLAUDE.md AGENT_GUIDE.md | \
  while read line; do
    file=$(echo $line | cut -d: -f1)
    link=$(echo $line | grep -o "(.*\.md" | tr -d '(')
    [ -f "$link" ] || echo "Broken: $file -> $link"
  done

# Check for outdated file paths in docs
grep -r "src/maze/.*\.py" docs/ README.md | \
  while read line; do
    path=$(echo $line | grep -o "src/maze/[^)]*\.py")
    [ -f "$path" ] || echo "Outdated path: $line"
  done
```

**CHANGELOG Health**:

```bash
# Check if [Unreleased] has content
grep -A 10 "## \[Unreleased\]" CHANGELOG.md | grep -q "^-" || echo "CHANGELOG may need updates"

# Check if recent commits are documented
git log --since="1 week ago" --oneline | wc -l
# → If >5 commits but empty [Unreleased], likely missing entries
```

### 8.5 Git Health

**Branch Hygiene**:

```bash
# List stale branches (no commits in 30 days)
git for-each-ref --sort=-committerdate refs/heads/ \
  --format='%(committerdate:short) %(refname:short)' | \
  awk '$1 < "'$(date -v-30d +%Y-%m-%d)'" {print $2}'

# Merged branches not deleted
git branch --merged main | grep -v "main$"
# → Should delete these

# Unmerged feature branches (check status)
git branch --no-merged main
```

**Commit Quality**:

```bash
# Recent commits without conventional format
git log --oneline -20 | grep -v "^[a-f0-9]\+ \(feat\|fix\|refactor\|perf\|docs\|chore\):"
# → Investigate non-conventional commits

# Commits without issue references
git log --oneline -20 | grep -v "maze-"
# → Should be rare (most work tracked in Beads)
```

**Tag Consistency**:

```bash
# Check tags match CHANGELOG versions
git tag -l "v*" | sort -V | tail -n 5
grep "^## \[" CHANGELOG.md | head -n 6
# → Should align (same versions)

# Orphaned tags (version in tag but not CHANGELOG)
# Manual check
```

### 8.6 Dependency Health

**Check for Updates**:

```bash
# List outdated dependencies
uv pip list --outdated

# Security vulnerabilities (if available)
uv pip check
```

**Dependency Usage**:

```bash
# Find unused dependencies
# (manual: check if each in pyproject.toml is imported in src/)

# Check for version conflicts
uv pip install --dry-run
```

### 8.7 Agent Decision Audit

**Track Agent Decisions** (via mnemosyne):

```bash
# Recent agent decisions
mnemosyne recall -q "decided OR chose OR selected" \
  -n "project:maze" --min-importance 7 -l 10

# Decision patterns
mnemosyne recall -q "architecture decision" \
  -n "project:maze" --min-importance 8 -l 20

# Failed approaches (learnings)
mnemosyne recall -q "failed OR didn't work OR reverted" \
  -n "project:maze" -l 10
```

**Quality Gate Pass Rate** (via git log):

```bash
# Count commits with test failures in message
git log --all --grep="test.*fail" --oneline | wc -l

# Count performance improvements
git log --all --grep="Performance Impact" --oneline | wc -l

# Count reverts (high number = quality issues)
git log --all --grep="revert" --oneline | wc -l
```

---

## 9. Reference Tables

### 9.1 File Location Reference

| File Type | Location | Example |
|-----------|----------|---------|
| Core types | `src/maze/core/` | `types.py`, `constraints.py` |
| Base indexer | `src/maze/indexer/` | `base.py` |
| Language indexer | `src/maze/indexer/languages/` | `typescript.py`, `python.py` |
| Base type system | `src/maze/type_system/` | `base.py` |
| Language type system | `src/maze/type_system/languages/` | `typescript.py` |
| Grammars | `src/maze/synthesis/grammars/` | `typescript.lark` |
| Templates | `src/maze/synthesis/templates/` | `function.py.jinja` |
| Orchestrator base | `src/maze/orchestrator/` | `base.py` |
| Provider adapters | `src/maze/orchestrator/providers/` | `openai.py`, `vllm.py` |
| Validation | `src/maze/validation/` | `validator.py` |
| Repair | `src/maze/repair/` | `repair.py` |
| llguidance integration | `src/maze/integrations/llguidance/` | `adapter.py` |
| mnemosyne integration | `src/maze/integrations/mnemosyne/` | `client.py` |
| pedantic_raven integration | `src/maze/integrations/pedantic_raven/` | `validator.py` |
| RUNE integration | `src/maze/integrations/rune/` | `sandbox.py` |
| Public API | `src/maze/api/` | `sync.py`, `async_api.py` |
| Utilities | `src/maze/utils/` | `metrics.py`, `cache.py` |
| Unit tests | `tests/unit/{module}/` | `test_types.py` |
| Integration tests | `tests/integration/` | `test_llguidance.py` |
| E2E tests | `tests/e2e/` | `test_workflow.py` |
| Performance benchmarks | `benchmarks/` | `mask_computation.py` |
| Architecture docs | `docs/` | `architecture.md` |
| Specs | `specs/` or `specs/origin/` | `*.md` |

### 9.2 Conventional Commit Types

| Type | Description | Branch Prefix | Changelog Section | Beads Type |
|------|-------------|---------------|-------------------|------------|
| `feat` | New feature | `feature/` | Added | feature |
| `fix` | Bug fix | `fix/` | Fixed | bug |
| `refactor` | Code restructuring | `refactor/` | Changed | task |
| `perf` | Performance improvement | `perf/` | Performance | task |
| `docs` | Documentation only | `docs/` | Documentation | task |
| `test` | Test additions/changes | `test/` | (none) | task |
| `chore` | Tooling, dependencies | `chore/` | (none) | task |
| `style` | Code style (no logic change) | `style/` | (none) | task |
| `build` | Build system changes | `build/` | (none) | task |
| `ci` | CI/CD changes | `ci/` | (none) | task |

### 9.3 Beads Issue Types and Priorities

| Type | Description | Typical Priority | Typical Timeline |
|------|-------------|------------------|------------------|
| epic | Large multi-task effort | 1-2 | Weeks to months |
| feature | New functionality | 1-2 | Days to weeks |
| bug | Defect or error | 0-2 | Hours to days |
| task | General work item | 2-3 | Hours to days |

| Priority | Label | Description | Response Time |
|----------|-------|-------------|---------------|
| 0 | Critical | Blocking, production down | Immediate |
| 1 | High | Important feature/fix | Within days |
| 2 | Medium | Normal priority | Within weeks |
| 3 | Low | Nice-to-have | When available |

### 9.4 Documentation Update Matrix

| Change Type | README.md | CLAUDE.md | CONTRIBUTING.md | docs/architecture.md | CHANGELOG.md |
|-------------|-----------|-----------|-----------------|---------------------|--------------|
| Public API change | ✅ API Reference | - | - | ✅ Core Components | ✅ Added/Changed |
| Architecture change | ✅ Architecture | - | - | ✅ Full update | ✅ Changed |
| Performance change | ✅ Performance table | ✅ Targets | ✅ Validation | ✅ Performance Arch | ✅ Performance |
| Constraint type added | ✅ Constraint Hierarchy | ✅ Constraint Dev | - | ✅ Constraint System | ✅ Added |
| Language indexer added | ✅ Supported Languages | ✅ Indexer Guidelines | - | ✅ Indexer Framework | ✅ Added |
| Provider adapter added | ✅ Provider Support | - | - | ✅ Provider Adapters | ✅ Added |
| Integration added | ✅ Integrations | ✅ Integration Guidelines | ✅ Integration section | ✅ Integration Arch | ✅ Added |
| Workflow change | - | ✅ Work Plan Protocol | ✅ Workflow | - | ✅ Changed |
| Testing requirement change | - | ✅ Testing Protocols | ✅ Testing Requirements | - | ✅ Changed |
| Bug fix | - | - | - | - | ✅ Fixed |
| Dependency change | ✅ Installation | - | - | - | ✅ Changed |

### 9.5 Performance Targets Reference

| Metric | Target | Current (v0.1.0) | How to Measure | How to Update Docs |
|--------|--------|------------------|----------------|---------------------|
| Token mask computation (p99) | <100μs | 50μs | `pytest -m performance` | README.md performance table |
| Grammar compilation | <50ms | 42ms | `pytest -m performance` | README.md performance table |
| Type error reduction | >75% | 94% | Manual benchmark | README.md performance table |
| Compilation success rate | >95% | 97% | E2E tests | README.md performance table |
| Memory usage | <1GB | 600MB | Profiling | README.md performance table |
| Cache hit rate | >70% | 89% | Adapter metrics | README.md performance table |
| Indexing speed | >1000 symbols/sec | 1000 | Indexer benchmarks | Per-language in docs |
| Type search | <1ms | TBD (Phase 3) | Type system benchmarks | Phase 3 update |

### 9.6 Quality Gate Checklist Reference

| Gate | Check Command | Pass Criteria | Blocking |
|------|---------------|---------------|----------|
| Tests | `uv run pytest tests/unit -v` | All pass | ✅ Yes |
| Performance | `uv run pytest -m performance -v` | All targets met | ✅ Yes |
| Coverage | `uv run pytest --cov=src/maze --cov-fail-under=70` | ≥70% overall | ✅ Yes |
| Type checking | `uv run mypy src/` | No errors | ✅ Yes |
| Formatting | `uv run black src/ tests/ --check` | No changes needed | ✅ Yes |
| Linting | `uv run ruff src/ tests/` | No errors | ✅ Yes |
| Documentation | Manual review | Updated per matrix | ✅ Yes |
| Changelog | Manual review | Entry in [Unreleased] | ✅ Yes |
| Beads state | `bd show {issue-id}` | Issue closed | ⚠️ Recommended |
| mnemosyne storage | Manual | Key decisions stored | ⚠️ Recommended |

### 9.7 mnemosyne Importance Levels

| Level | Usage | Examples | When to Use |
|-------|-------|----------|-------------|
| 10 | Critical, rare | "Chose event sourcing for audit trail (regulatory requirement)" | Fundamental architecture decisions |
| 9 | Very important | "Released v1.0.0", "Major API redesign" | Releases, breaking changes, major milestones |
| 8 | Important | "Provider adapter pattern for LLM backends", "Bug: race condition in cache" | Architecture patterns, bug root causes, key implementation decisions |
| 7 | Useful | "Grammar caching reduced p99 from 120μs to 45μs", "Refactored indexer structure" | Performance insights, refactoring rationale, minor patterns |
| 6 | Nice-to-know | "TypeScript indexer uses tree-sitter" | General implementation details |
| 5 and below | Noise | Don't store | Too low-value |

### 9.8 Integration System Reference

| System | Purpose | Integration Location | Key Patterns | Documentation |
|--------|---------|---------------------|--------------|---------------|
| llguidance | Constraint enforcement via token masking | `src/maze/integrations/llguidance/` | Grammar compilation, mask caching, provider adapters | CLAUDE.md §3.1, docs/architecture.md |
| mnemosyne | Persistent memory and orchestration | `src/maze/integrations/mnemosyne/` | Namespace: `project:maze:{component}`, importance 7-10 | CLAUDE.md §3.2, AGENT_GUIDE.md §5.2 |
| pedantic_raven | Deep semantic validation | `src/maze/integrations/pedantic_raven/` | Property specs, validation modes | CLAUDE.md §3.3 |
| RUNE | Sandboxed code execution | `src/maze/integrations/rune/` | Resource limits, isolation, diagnostics | CLAUDE.md §3.4, docs/architecture.md |

---

## 10. Quick Command Reference

### 10.1 Workflow Commands

```bash
# Start new feature
git checkout -b feature/{name}
bd create "Title" -t feature -p 1 --json
bd update {id} --status in_progress --json

# Code and test
{implement code}
git add . && git commit -m "{message}"
uv run pytest

# Document and PR
{update docs per §2.2}
git push -u origin feature/{name}
gh pr create --title "{title}" --body "{body}"

# After merge
bd close {id} --reason "Complete" --json
git branch -d feature/{name}
mnemosyne remember -c "{insight}" -n "project:maze" -i 8 -t "{tags}"
```

### 10.2 Quality Check Commands

```bash
# Setup
uv pip install -e ".[dev]"

# Full quality check
uv run black src/ tests/
uv run ruff src/ tests/
uv run mypy src/
uv run pytest tests/unit -v
uv run pytest -m performance -v
uv run pytest --cov=src/maze --cov-report=term --cov-fail-under=70

# Testing (comprehensive)
uv run pytest                                    # All tests
uv run pytest tests/unit -v                      # Unit tests
uv run pytest tests/integration -v               # Integration tests
uv run pytest tests/e2e -v                       # E2E tests
uv run pytest -m performance -v                  # Performance benchmarks
uv run pytest --cov=maze --cov-report=html      # Coverage report

# Performance Validation
uv run python benchmarks/mask_computation.py     # Mask benchmark
uv run python benchmarks/end_to_end.py          # E2E benchmark
uv run python benchmarks/compare_engines.py     # Engine comparison
uv run python benchmarks/baseline.py --save     # Save baseline
uv run python benchmarks/baseline.py --compare  # Compare to baseline
```

### 10.3 Beads Commands

```bash
# Discovery
bd ready --json --limit 5
bd list --status open --type bug --priority 0 --json
bd show {id}

# Execution
bd create "{title}" -t {type} -p {priority} --json
bd update {id} --status in_progress --json
bd close {id} --reason "Complete" --json

# Dependencies
bd dep add {id} {blocker-id} --type blocks
bd dep tree {id}

# Health
bd doctor
bd info --json
```

### 10.4 Git Commands

```bash
# Branching
git checkout -b {type}/{name}
git push -u origin {type}/{name}

# Committing
git add {files}
git commit -m "{conventional commit}"
git log -1 --oneline

# Release
git tag -a v{X.Y.Z} -m "Release v{X.Y.Z}: {summary}"
git push origin main --tags
gh release create v{X.Y.Z} --title "{title}" --notes-file {file}

# Cleanup
git branch --merged main | grep -v "main$" | xargs git branch -d
```

### 10.5 mnemosyne Commands

```bash
# Store
mnemosyne remember -c "{content}" \
  -n "project:maze:{component}" -i {7-10} -t "{tags}" \
  --context "{context}"

# Recall
mnemosyne recall -q "{query}" -n "project:maze" -l {5-10}
mnemosyne recall -q "{query}" --min-importance 7 -l 10

# Evolution
mnemosyne evolve
```

### 10.6 Documentation Commands

```bash
# Check for broken paths
grep -r "src/maze/.*\.py" docs/ README.md | \
  while read line; do
    path=$(echo $line | grep -o "src/maze/[^)]*\.py")
    [ -f "$path" ] || echo "Broken: $line"
  done

# Update CHANGELOG
# Edit manually under [Unreleased]

# Verify cross-references
grep -r "\[.*\](.*\.md" docs/ README.md | {verify links exist}
```

### 10.7 Repository Tidying Commands

```bash
# Find missing __init__.py
find src/maze -type d -not -path "*/.*" -exec test ! -e "{}/__init__.py" \; -print

# Non-destructive move
git mv {source} {target}
{update all references}
git commit -m "refactor: Move {file} to {location}"

# Verify imports
uv run python -c "import maze; print('OK')"
uv run pytest tests/unit -v
```

---

## 11. Implementation Patterns

### 11.1 Incremental Refinement Pattern

**Use Case**: Iteratively tighten constraints based on validation failures

**When to Use**: Complex tasks where optimal constraints unknown upfront

**Implementation**:

```python
async def incremental_refinement(prompt: str, spec: Specification):
    """Start loose, tighten on failures."""

    # Start with syntactic only
    constraints = ConstraintSet()
    constraints.add(SyntacticConstraint.from_language(spec.language))

    for attempt in range(3):
        # Generate with current constraints
        code = await generate(prompt, constraints)

        # Validate
        result = await validate(code, spec)

        if result.passed:
            # Success - store pattern
            await memory.store_constraint_pattern(
                pattern=constraints.to_pattern(),
                success=True,
                metrics={"attempts": attempt + 1}
            )
            return code

        # Tighten constraints based on failure type
        if result.type_errors:
            # Add type constraints
            constraints.add(TypeConstraint(
                expected_type=spec.return_type,
                context=spec.type_context
            ))

        if result.semantic_errors:
            # Add semantic constraints
            for error in result.semantic_errors:
                constraints.add(semantic_constraint_from_error(error))

    # Failed after 3 attempts
    return None
```

**Workflow Integration**:
1. Start with syntactic constraints only
2. Generate and validate
3. If fails, analyze failure type
4. Add appropriate constraint tier (type, semantic, contextual)
5. Retry with tightened constraints
6. Store successful pattern in mnemosyne

---

### 11.2 Speculative Generation Pattern

**Use Case**: Generate multiple candidates in parallel, select best

**When to Use**: Performance is less critical than correctness

**Implementation**:

```python
async def speculative_generation(prompt: str, spec: Specification):
    """Generate multiple candidates, validate concurrently."""

    # Create constraint variations
    constraint_sets = [
        create_loose_constraints(spec),
        create_medium_constraints(spec),
        create_strict_constraints(spec),
    ]

    # Generate in parallel
    tasks = [
        generate(prompt, constraints)
        for constraints in constraint_sets
    ]
    candidates = await asyncio.gather(*tasks)

    # Validate in parallel
    validation_tasks = [
        validate(code, spec)
        for code in candidates
    ]
    results = await asyncio.gather(*validation_tasks)

    # Select best (first that passes, or highest score)
    for code, result in zip(candidates, results):
        if result.passed:
            return code

    # None passed - return best partial
    return max(zip(candidates, results), key=lambda x: x[1].score)[0]
```

**Workflow Integration**:
1. Create 3 constraint variations (loose, medium, strict)
2. Generate all candidates in parallel
3. Validate all candidates in parallel
4. Return first passing, or highest-scoring partial
5. Store best approach in mnemosyne

---

### 11.3 Typed Hole Filling Pattern

**Use Case**: Complete partial code with type-directed search

**When to Use**: Completing functions, filling in implementation details

**Implementation**:

```python
async def fill_typed_hole(code_with_hole: str, hole_type: Type):
    """Fill hole using type inhabitation."""

    # Extract context around hole
    context = extract_context(code_with_hole)
    type_context = infer_type_context(context)

    # Find expressions matching hole type
    solver = InhabitationSolver()
    valid_expressions = solver.find_valid_expressions(
        expected_type=hole_type,
        context=type_context
    )

    # Rank by likelihood and type fitness
    ranked = rank_expressions(valid_expressions, context)

    # Try each candidate
    for expr in ranked[:5]:  # Top 5
        completed = code_with_hole.replace("/*__HOLE__*/", expr)

        # Validate
        result = await validate(completed, spec)
        if result.passed:
            return completed

    # No valid completion found
    return None
```

**Workflow Integration**:
1. Identify typed hole marker (`/*__HOLE__*/`)
2. Extract surrounding context
3. Use type inhabitation solver to find valid expressions
4. Rank candidates by likelihood and type fitness
5. Try top N candidates with validation
6. Return first valid completion

---

### 11.4 Adaptive Constraint Weighting Pattern

**Use Case**: Learn from project to weight soft constraints

**When to Use**: Project-specific generation, adapting to codebase conventions

**Implementation**:

```python
async def adaptive_weighting(prompt: str, spec: Specification):
    """Weight constraints based on project patterns."""

    # Recall successful patterns from this project
    patterns = await memory.recall_similar_contexts(
        query=prompt,
        namespace=f"project:maze:{spec.language}",
        limit=10
    )

    # Create contextual constraints weighted by success
    contextual = ContextualConstraint(weight=0.5)

    for pattern in patterns:
        success_rate = pattern.metadata.get("success_rate", 0.5)
        contextual.add_pattern(
            pattern=pattern.content,
            weight=success_rate
        )

    # Combine with hard constraints
    constraints = ConstraintSet()
    constraints.add(SyntacticConstraint.from_language(spec.language))
    constraints.add(contextual)

    # Generate with weighted constraints
    code = await generate(prompt, constraints)

    # Update weights based on outcome
    result = await validate(code, spec)
    await update_pattern_weights(patterns, result.passed)

    return code
```

**Workflow Integration**:
1. Recall similar successful patterns from mnemosyne
2. Create contextual constraints weighted by success rate
3. Combine with hard constraints (syntactic, type)
4. Generate with weighted constraints
5. Validate and update pattern weights
6. Store updated success rates in mnemosyne

**mnemosyne Storage**:
```bash
# Store pattern with success metrics
mnemosyne remember -c "Pattern {name}: {success_rate}% success in {context}" \
  -n "project:maze:{language}:{pattern-category}" \
  -i 8 \
  -t "pattern,{language},success"
```

---

### 11.5 Pattern Selection Guide

| Scenario | Recommended Pattern | Rationale |
|----------|-------------------|-----------|
| First attempt at task type | Incremental Refinement | Unknown optimal constraints |
| Critical correctness requirement | Speculative Generation | Multiple attempts, select best |
| Partial code completion | Typed Hole Filling | Type-guided search efficient |
| Project-specific style | Adaptive Weighting | Learn from codebase patterns |
| Time-constrained task | Incremental Refinement | Fastest to first success |
| Complex type requirements | Typed Hole Filling | Leverage type system |
| Learning new domain | Adaptive Weighting | Build pattern library |

---

## 12. Enforcement and CI/CD

### 12.1 Automated Quality Gates

**CI/CD Workflow** (`.github/workflows/maze-ci.yml`):

```yaml
name: Maze CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v1

      - name: Install dependencies
        run: uv pip install -e ".[dev]"

      - name: Run tests
        run: uv run pytest tests/unit -v

      - name: Check coverage
        run: |
          uv run pytest --cov=maze --cov-report=term --cov-fail-under=85

      - name: Performance benchmarks
        run: |
          uv run pytest -m performance -v
          # Assert targets met (handled in test assertions)

      - name: Type checking
        run: uv run mypy src/

      - name: Linting
        run: |
          uv run black --check src/ tests/
          uv run ruff src/ tests/
```

**When to Update**:
- New quality gate added → Add step to CI
- Coverage target changes → Update `--cov-fail-under`
- New linter/formatter → Add to workflow

---

### 12.2 Pre-Commit Hooks

**Location**: `.git/hooks/pre-commit`

**Implementation**:

```bash
#!/bin/bash

# Format check
uv run black --check src/ tests/ || {
    echo "❌ Code not formatted. Run: uv run black src/ tests/"
    exit 1
}

# Lint check
uv run ruff src/ tests/ || {
    echo "❌ Linting failed"
    exit 1
}

# Fast tests only
uv run pytest tests/unit -m "not slow and not performance" || {
    echo "❌ Tests failed"
    exit 1
}

echo "✅ Pre-commit checks passed"
```

**Installation**:

```bash
# Make hook executable
chmod +x .git/hooks/pre-commit

# Verify
git commit -m "test" --dry-run
```

**Bypassing** (emergency only):
```bash
# Skip pre-commit for emergency fix
git commit --no-verify -m "fix: Emergency hotfix"

# Create follow-up issue to fix properly
bd create "Clean up emergency commit {hash}" -t task -p 1
```

---

### 12.3 Performance Regression Detection

**Baseline Tracking**:

```bash
# Save baseline before changes
uv run python benchmarks/baseline.py --save baseline.json

# After changes, compare
uv run python benchmarks/baseline.py --compare baseline.json
```

**Baseline Script** (`benchmarks/baseline.py`):

```python
#!/usr/bin/env python3
"""Save and compare performance baselines."""
import json
import argparse
from pathlib import Path

def measure_performance():
    """Measure all performance metrics."""
    from maze.integrations.llguidance import LLGuidanceAdapter
    import statistics
    import time

    adapter = LLGuidanceAdapter(enable_profiling=True)
    # ... measurement code ...

    return {
        "p99_mask_us": p99,
        "cache_hit_rate": hit_rate,
        "grammar_compile_ms": compile_time,
        # ... other metrics ...
    }

def save_baseline(metrics, path="baseline.json"):
    """Save metrics as baseline."""
    Path(path).write_text(json.dumps(metrics, indent=2))
    print(f"✅ Baseline saved to {path}")

def compare_baseline(metrics, baseline_path="baseline.json"):
    """Compare current metrics to baseline."""
    baseline = json.loads(Path(baseline_path).read_text())

    regressions = []
    for key, current in metrics.items():
        previous = baseline.get(key)
        if previous is None:
            continue

        # Calculate change
        change = ((current - previous) / previous) * 100

        # Check thresholds (from CLAUDE.md)
        if change > 10:  # >10% degradation is warning
            regressions.append(f"⚠️  {key}: {previous} → {current} ({change:+.1f}%)")
        elif change > 25:  # >25% degradation is failure
            regressions.append(f"❌ {key}: {previous} → {current} ({change:+.1f}%)")
        elif change < -10:  # >10% improvement
            regressions.append(f"✅ {key}: {previous} → {current} ({change:+.1f}%)")

    if any(line.startswith("❌") for line in regressions):
        print("\n".join(regressions))
        exit(1)  # Fail build
    else:
        print("\n".join(regressions) if regressions else "✅ No regressions")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", help="Save baseline to file")
    parser.add_argument("--compare", help="Compare to baseline file")
    args = parser.parse_args()

    metrics = measure_performance()

    if args.save:
        save_baseline(metrics, args.save)
    elif args.compare:
        compare_baseline(metrics, args.compare)
    else:
        print(json.dumps(metrics, indent=2))
```

**Usage in Workflow**:
```bash
# Before feature work
uv run python benchmarks/baseline.py --save before.json

# After feature complete
uv run python benchmarks/baseline.py --compare before.json
# → Fails if >25% regression, warns if >10%
```

---

### 12.4 Quality Gate Enforcement Matrix

| Gate | Command | Pass Criteria | Enforcement Level | Bypass Allowed |
|------|---------|---------------|-------------------|----------------|
| Unit tests | `uv run pytest tests/unit -v` | All pass | ✅ CI required | ❌ Never |
| Performance | `uv run pytest -m performance -v` | All targets met | ✅ CI required | ❌ Never |
| Coverage | `uv run pytest --cov=maze --cov-fail-under=70` | ≥70% overall | ✅ CI required | ⚠️  Emergency only |
| Type checking | `uv run mypy src/` | No errors | ✅ CI required | ⚠️  Emergency only |
| Formatting | `uv run black --check src/ tests/` | No changes needed | ✅ Pre-commit + CI | ⚠️  Emergency only |
| Linting | `uv run ruff src/ tests/` | No errors | ✅ Pre-commit + CI | ⚠️  Emergency only |
| Documentation | Manual review | Updated per matrix | ⚠️  PR review | ❌ Never |
| Changelog | Manual review | Entry in [Unreleased] | ⚠️  PR review | ⚠️  Docs-only changes |

**Emergency Bypass Protocol**:
1. Only for critical production issues
2. Must create follow-up Beads issue immediately
3. Must link bypass commit to follow-up issue
4. Follow-up must be priority 0 or 1
5. Store incident in mnemosyne with high importance (9)

```bash
# Emergency bypass
git commit --no-verify -m "fix: Critical production issue {brief}

EMERGENCY BYPASS: Pre-commit checks skipped
Follow-up issue: maze-{id}"

# Immediately create follow-up
bd create "Fix quality violations from emergency commit {hash}" \
  -t bug -p 0 --json

# Store incident
mnemosyne remember -c "Emergency bypass for {issue}: {reason}" \
  -n "project:maze" -i 9 -t "incident,bypass,emergency"
```

---

### 12.5 Release Quality Checklist

**Pre-Release Verification** (from §2.3):

```bash
#!/bin/bash
# release-check.sh

set -e

echo "🔍 Running release quality checks..."

# 1. All tests
echo "Running tests..."
uv run pytest || exit 1

# 2. Performance benchmarks
echo "Running performance benchmarks..."
uv run pytest -m performance -v || exit 1

# 3. Coverage
echo "Checking coverage..."
uv run pytest --cov=maze --cov-report=term --cov-fail-under=70 || exit 1

# 4. Type checking
echo "Type checking..."
uv run mypy src/ || exit 1

# 5. Formatting
echo "Checking formatting..."
uv run black --check src/ tests/ || exit 1

# 6. Linting
echo "Linting..."
uv run ruff src/ tests/ || exit 1

# 7. Documentation
echo "Checking documentation..."
[ -f CHANGELOG.md ] || { echo "❌ CHANGELOG.md missing"; exit 1; }
grep -q "\[Unreleased\]" CHANGELOG.md || { echo "❌ No [Unreleased] section"; exit 1; }

# 8. No TODO/FIXME
echo "Checking for TODO/FIXME..."
! grep -r "TODO\|FIXME" src/ && echo "✅ No TODO/FIXME found" || {
    echo "❌ Found TODO/FIXME comments. Create Beads issues instead."
    exit 1
}

# 9. Beads state
echo "Checking Beads state..."
bd ready --json | jq 'length' > /dev/null || { echo "⚠️  Beads check failed"; }

echo "✅ All release quality checks passed!"
```

**Usage**:
```bash
# Before release
./release-check.sh

# If passes, proceed with release
git tag -a v0.2.0 -m "Release v0.2.0"
```

---

## Conclusion

This guide provides decision trees, workflows, templates, and reference tables for agentic systems working on Maze. Key principles:

1. **Decision Trees** route tasks correctly
2. **Workflows** ensure consistent execution
3. **Templates** maintain quality and format
4. **Tidying** keeps repository organized
5. **Integration** leverages CLAUDE.md, mnemosyne, Beads, Git
6. **Scenarios** demonstrate patterns
7. **Anti-Patterns** prevent mistakes
8. **Observability** tracks health
9. **References** provide quick lookups
10. **Implementation Patterns** provide tested code examples
11. **Enforcement** automates quality gates

**Remember**:
- Use Task Classification Tree (§1.1) for every request
- Follow Work Plan Protocol (CLAUDE.md §1) for all work
- Update documentation via trigger tree (§1.2)
- Preserve git history with non-destructive moves (§4)
- Store insights in mnemosyne (§5.2)
- Track work in Beads (§5.3)
- Check quality gates before completion (§9.6)

For detailed development protocols, see CLAUDE.md.
For user-facing documentation, see README.md.
For contribution guidelines, see CONTRIBUTING.md.
