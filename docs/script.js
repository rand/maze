/**
 * MAZE: Adaptive Constrained Code Generation
 * Interactive features for GitHub Pages site
 */

(function() {
    'use strict';

    // ================================
    // Smooth Scrolling
    // ================================
    function initSmoothScrolling() {
        const links = document.querySelectorAll('a[href^="#"]');

        links.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');

                // Skip empty anchors
                if (href === '#') return;

                const target = document.querySelector(href);

                if (target) {
                    e.preventDefault();

                    const navHeight = document.querySelector('.navbar').offsetHeight;
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });

                    // Update URL without jumping
                    history.pushState(null, null, href);
                }
            });
        });
    }

    // ================================
    // Active Navigation Highlighting
    // ================================
    function initActiveNavigation() {
        const sections = document.querySelectorAll('.section[id]');
        const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

        function highlightNavigation() {
            const scrollPosition = window.scrollY + 100;

            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                const sectionId = section.getAttribute('id');

                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === `#${sectionId}`) {
                            link.classList.add('active');
                        }
                    });
                }
            });
        }

        window.addEventListener('scroll', highlightNavigation);
        highlightNavigation(); // Initial call
    }

    // ================================
    // Copy Code Blocks
    // ================================
    function initCodeCopying() {
        const codeBlocks = document.querySelectorAll('pre code');

        codeBlocks.forEach(block => {
            const pre = block.parentElement;
            const wrapper = document.createElement('div');
            wrapper.className = 'code-wrapper';

            const button = document.createElement('button');
            button.className = 'copy-button';
            button.textContent = 'Copy';
            button.setAttribute('aria-label', 'Copy code to clipboard');

            // Wrap pre with div and add button
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);
            wrapper.appendChild(button);

            button.addEventListener('click', async () => {
                try {
                    const code = block.textContent;
                    await navigator.clipboard.writeText(code);

                    button.textContent = 'Copied!';
                    button.classList.add('copied');

                    setTimeout(() => {
                        button.textContent = 'Copy';
                        button.classList.remove('copied');
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy code:', err);
                    button.textContent = 'Failed';

                    setTimeout(() => {
                        button.textContent = 'Copy';
                    }, 2000);
                }
            });
        });
    }

    // ================================
    // Scroll to Top Button
    // ================================
    function initScrollToTop() {
        const button = document.createElement('button');
        button.className = 'scroll-to-top';
        button.innerHTML = '↑';
        button.setAttribute('aria-label', 'Scroll to top');
        button.style.display = 'none';
        document.body.appendChild(button);

        window.addEventListener('scroll', () => {
            if (window.scrollY > 500) {
                button.style.display = 'flex';
            } else {
                button.style.display = 'none';
            }
        });

        button.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // ================================
    // External Link Indicators
    // ================================
    function initExternalLinks() {
        const links = document.querySelectorAll('a[href^="http"]');

        links.forEach(link => {
            // Skip links within same domain
            if (link.hostname === window.location.hostname) return;

            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        });
    }

    // ================================
    // Lazy Load Images
    // ================================
    function initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const images = document.querySelectorAll('img[data-src]');

            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        }
    }

    // ================================
    // Keyboard Navigation
    // ================================
    function initKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // ESC to blur active element
            if (e.key === 'Escape') {
                if (document.activeElement) {
                    document.activeElement.blur();
                }
            }
        });
    }

    // ================================
    // Mobile Menu Toggle (if needed later)
    // ================================
    function initMobileMenu() {
        // Placeholder for future mobile menu functionality
        // Currently the nav links are hidden on mobile via CSS
        // Could add hamburger menu here if needed
    }

    // ================================
    // Add CSS for dynamic elements
    // ================================
    function addDynamicStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .code-wrapper {
                position: relative;
                margin-bottom: 1rem;
            }

            .copy-button {
                position: absolute;
                top: 0.5rem;
                right: 0.5rem;
                padding: 0.5rem 1rem;
                background-color: rgba(255, 255, 255, 0.9);
                color: #1E3A8A;
                border: 1px solid #1E3A8A;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.85rem;
                font-weight: 600;
                transition: all 0.2s ease;
                z-index: 10;
            }

            .copy-button:hover {
                background-color: #1E3A8A;
                color: white;
            }

            .copy-button.copied {
                background-color: #10B981;
                border-color: #10B981;
                color: white;
            }

            .scroll-to-top {
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                width: 48px;
                height: 48px;
                background-color: #1E3A8A;
                color: white;
                border: none;
                border-radius: 50%;
                font-size: 1.5rem;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                transition: all 0.2s ease;
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .scroll-to-top:hover {
                background-color: #3B82F6;
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
            }

            .nav-links a.active {
                color: #F59E0B;
            }

            @media (max-width: 768px) {
                .copy-button {
                    top: 0.25rem;
                    right: 0.25rem;
                    padding: 0.4rem 0.8rem;
                    font-size: 0.75rem;
                }

                .scroll-to-top {
                    bottom: 1rem;
                    right: 1rem;
                    width: 40px;
                    height: 40px;
                    font-size: 1.25rem;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // ================================
    // Analytics (placeholder)
    // ================================
    function initAnalytics() {
        // Placeholder for analytics tracking
        // Could add Google Analytics, Plausible, etc.
    }

    // ================================
    // Initialize Everything
    // ================================
    function init() {
        // Add dynamic styles first
        addDynamicStyles();

        // Initialize all features
        initSmoothScrolling();
        initActiveNavigation();
        initCodeCopying();
        initScrollToTop();
        initExternalLinks();
        initLazyLoading();
        initKeyboardNavigation();
        initMobileMenu();
        initAnalytics();

        console.log('MAZE GitHub Pages site initialized');
    }

    // Run initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
