// Dynamic sidebar content based on scroll position
(function() {
    // Section-specific comments for MAZE (mix of technical + dry wit)
    const sectionComments = {
        'abstract': '// Compile constraints before decoding, not after',
        'paradigm': '// Because "just fix it later" is technical debt',
        'architecture': '// 5-stage pipeline: Index → Synthesize → Orchestrate → Validate → Repair',
        'constraints': '// 4 tiers: Syntax → Types → Semantics → Context',
        'integrations': '// Standing on the shoulders of giants (and Microsoft Research)',
        'status': '// Phase 3/6 complete • 60% validation coverage',
        'research': '// PLDI 2025 • OOPSLA 2024 • llguidance',
        'validation': '// 12K lines of Rust • Property tests FTW',
        'getting-started': '// cargo install --git ...'
    };

    // Subsection commentary (detected via nearest h3)
    const subsectionComments = {
        'Traditional Approach: Generate, Then Fix': '// Hope-driven development: generate → pray → patch',
        'MAZE Approach: Constrain, Then Generate': '// Constraint-driven: synthesize → decode → validate',
        'Stage 1: Context Indexer': '// Parse the world before constraining it',
        'Stage 2: Constraint Synthesis': '// CFG + types + tests = formal guarantees',
        'Stage 3: Decode Orchestrator': '// llguidance integration: <100μs constraint checks',
        'Stage 4: Post-Validation': '// Because compile-time constraints miss runtime state',
        'Stage 5: Repair Loop': '// When things go wrong, iterate (not panic)',
        'Tier 1: Syntactic Constraints': '// CFG: the bouncer at the syntax nightclub',
        'Tier 2: Type Constraints': '// Inhabitation search: find me a value of this type',
        'Tier 3: Semantic Constraints': '// Unit tests as executable specifications',
        'Tier 4: Contextual Constraints': '// Code review rules: no hardcoded credentials',
        'llguidance (Microsoft Research)': '// Fast CFG constraints for LLM decoding',
        'mnemosyne (Persistent Memory)': '// Remember what worked last time',
        'RUNE (Sandboxed Execution)': '// Run untrusted code, sleep soundly',
        'pedantic_raven (Quality Enforcement)': '// Semantic analysis: because linters lie',
        'Phases 1-3: Core System (Complete)': '// Context + constraints + orchestration ✓',
        'Phase 4: Validation and Repair (60 percent complete)': '// Property tests + repair loop in progress',
        'Phase 5: Adaptive Learning (Planned)': '// Learn from failures, adapt constraints',
        'Phase 6: Production (Planned)': '// Zero-downtime deployment, because YOLO is not a strategy',
        'Type-Constrained Code Generation (PLDI 2025)': '// Academic street cred: peer-reviewed',
        'Statically Contextualizing LLMs with Typed Holes (OOPSLA 2024)': '// More academic street cred',
        'LLGuidance (Microsoft Research)': '// The engine that makes sub-100μs possible',
        'Code Statistics': '// 12K lines Rust • 8K lines tests • 60% coverage',
        'Component Verification': '// Every claim tagged to source code'
    };

    function updateSidebarContent() {
        const sidebar = document.querySelector('.sidebar-tagline');
        if (!sidebar) return;

        // Get all sections and headings
        const sections = [...document.querySelectorAll('section[id]')];
        const headings = [...document.querySelectorAll('h2, h3')];

        // Account for navbar height
        const navbarHeight = 80;
        const scrollPosition = window.scrollY + navbarHeight + 50;

        // Find current section
        let currentSection = null;
        for (let i = sections.length - 1; i >= 0; i--) {
            if (scrollPosition >= sections[i].offsetTop) {
                currentSection = sections[i].id;
                break;
            }
        }

        // Find nearest h3 for more granular commentary
        let nearestH3 = null;
        let minDistance = Infinity;

        for (const heading of headings) {
            if (heading.tagName === 'H3') {
                const distance = Math.abs(scrollPosition - heading.offsetTop);
                if (distance < minDistance && scrollPosition >= heading.offsetTop - 100) {
                    minDistance = distance;
                    nearestH3 = heading.textContent.trim();
                }
            }
        }

        // Prioritize subsection commentary if we're close to an h3
        if (nearestH3 && subsectionComments[nearestH3] && minDistance < 300) {
            sidebar.textContent = subsectionComments[nearestH3];
        } else if (currentSection && sectionComments[currentSection]) {
            sidebar.textContent = sectionComments[currentSection];
        } else {
            sidebar.textContent = '// Constraint-driven LLM code generation';
        }
    }

    // Initialize on page load
    function init() {
        updateSidebarContent();

        // Update on scroll with throttling
        let ticking = false;
        window.addEventListener('scroll', function() {
            if (!ticking) {
                window.requestAnimationFrame(function() {
                    updateSidebarContent();
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    // Run on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
