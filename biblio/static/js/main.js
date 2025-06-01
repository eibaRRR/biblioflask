// biblio/static/js/main.js - Version créative (améliorée)

document.addEventListener('DOMContentLoaded', function() {

    // --- 1. GESTION DU THÈME SOMBRE/CLAIR ---
    const themeToggle = document.querySelector('#theme-switch-checkbox');
    const currentTheme = localStorage.getItem('theme');

    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        if (themeToggle) {
            themeToggle.checked = theme === 'dark';
        }
    };

    if (currentTheme) {
        applyTheme(currentTheme);
    } else {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(prefersDark ? 'dark' : 'light');
    }

    if (themeToggle) {
        themeToggle.addEventListener('change', function(e) {
            const newTheme = e.target.checked ? 'dark' : 'light';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // --- 2. RECHERCHE EN TEMPS RÉEL ---
    const searchInput = document.querySelector('#searchInput');
    const resultsContainer = document.querySelector('#realtime-results-container');
    const defaultContent = document.querySelector('#default-content');
    let debounceTimer;

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) {
                if (resultsContainer) resultsContainer.innerHTML = '';
                if (defaultContent) defaultContent.style.display = 'block';
                if (defaultContent) observeAnimatedElements(defaultContent.querySelectorAll('.book-card-wrapper'));
                return;
            }

            debounceTimer = setTimeout(() => {
                showSkeletonLoader(); 
                fetch(`/search_realtime?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (defaultContent) defaultContent.style.display = 'none';
                        renderRealtimeResults(data);
                    })
                    .catch(error => console.error('Erreur lors de la recherche:', error));
            }, 300);
        });
    }

    function showSkeletonLoader() {
        if (!resultsContainer) return;
        if (defaultContent) defaultContent.style.display = 'none';

        const skeletonHtml = `
            <div class="col book-card-wrapper">
                <div class="skeleton-card">
                    <div class="skeleton-image"></div>
                    <div class="skeleton-body">
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line skeleton-line-short"></div>
                    </div>
                </div>
            </div>
        `.repeat(4);

        resultsContainer.innerHTML = `
            <div class="container mt-4">
                <h2 class="genre-title mb-4"><span>Recherche en cours...</span></h2>
                <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">${skeletonHtml}</div>
            </div>`;
    }

    function renderRealtimeResults(livres) {
        if (!resultsContainer) return;
        
        if (livres.length === 0) {
            resultsContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-search-minus fa-3x text-muted mb-3"></i>
                    <h4 class="text-secondary">Aucun livre ne correspond à votre recherche.</h4>
                    <p class="text-muted">Essayez avec d'autres mots-clés.</p>
                </div>`;
            return;
        }
        
        const starRating = (note) => {
            let stars = '';
            for (let i = 1; i <= 5; i++) {
                stars += `<i class="fa-star ${i <= note ? 'fas' : 'far'}"></i>`;
            }
            return `<div class="star-rating mb-1">${stars}</div>`;
        };

        const html = livres.map(livre => `
            <div class="col book-card-wrapper">
                <div class="card h-100 book-card shadow-sm">
                    <a href="${livre.details_url}" class="text-decoration-none book-card-image-link">
                        <img src="${livre.image_url}" 
                             class="card-img-top" 
                             alt="Couverture de ${livre.titre}"
                             onerror="this.onerror=null; this.src='/static/images/default_cover_creative.png';">
                    </a>
                    <div class="card-body d-flex flex-column">
                        <div class="flex-grow-1 mb-2">
                            ${starRating(livre.note)}
                            <a href="${livre.details_url}" class="text-decoration-none">
                                <h5 class="card-title mb-1">${livre.titre}</h5>
                            </a>
                            <h6 class="card-subtitle text-muted small">par ${livre.auteur}</h6>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent border-top-0 pt-2 pb-3 px-3">
                        <a href="${livre.details_url}" class="btn btn-sm btn-outline-primary w-100 details-button">
                            Voir les détails <i class="fas fa-arrow-right ms-1"></i>
                        </a>
                    </div>
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = `
            <div class="container mt-4">
                <h2 class="genre-title mb-4"><span>Résultats de la recherche</span></h2>
                <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">${html}</div>
            </div>`;
        
        observeAnimatedElements(resultsContainer.querySelectorAll('.book-card-wrapper'));
    }

    // --- 3. ALERTE DE SUPPRESSION (SweetAlert2) ---
    document.body.addEventListener('click', function(event) {
        const deleteButton = event.target.closest('.delete-btn');
        if (deleteButton) {
            event.preventDefault();
            const bookTitle = deleteButton.dataset.bookTitle || "ce livre";
            const deleteUrl = deleteButton.href;

            Swal.fire({
                title: 'Êtes-vous sûr ?',
                text: `Voulez-vous vraiment supprimer "${bookTitle}" ? Cette action est irréversible.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: 'var(--danger-color, #FF3B30)',
                cancelButtonColor: 'var(--text-secondary, #6c757d)',
                confirmButtonText: 'Oui, supprimer !',
                cancelButtonText: 'Annuler',
                customClass: {
                    popup: 'swal-custom-popup',
                    title: 'swal-custom-title',
                    htmlContainer: 'swal-custom-html'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = deleteUrl;
                }
            });
        }
    });
    
    const style = document.createElement('style');
    style.textContent = `
        .swal-custom-popup {
            background-color: var(--surface-color) !important;
            color: var(--text-primary) !important;
            border-radius: var(--radius-xl) !important; /* Utilisation variable CSS */
        }
        .swal-custom-title {
            color: var(--text-primary) !important;
        }
        .swal-custom-html {
             color: var(--text-secondary) !important;
        }
    `;
    document.head.appendChild(style);

    // --- 4. ANIMATION AU SCROLL (Intersection Observer) ---
    const observeAnimatedElements = (elements) => {
        if (!elements || elements.length === 0) return;

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0) scale(1)';
                    entry.target.style.transition = 'opacity 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275), transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                    obs.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: "0px 0px -50px 0px"
        });

        elements.forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(60px) scale(0.95)';
            observer.observe(element);
        });
    };
    
    observeAnimatedElements(document.querySelectorAll('#default-content .book-card-wrapper'));
    // Observer également les recommandations sur la page de détails si elles existent
    observeAnimatedElements(document.querySelectorAll('.recommendations-section .book-card-wrapper'));


    // --- 5. EFFET PARALLAXE SUR LA SECTION HERO ---    
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        window.addEventListener('scroll', function() {
            const offset = window.pageYOffset;
            heroSection.style.backgroundPositionY = offset * 0.4 + 'px'; // Effet un peu plus subtil
        });
    }
    
    // --- NOUVEAU : BOUTON DE RETOUR EN HAUT DE PAGE ---
    const scrollToTopBtn = document.createElement('button');
    scrollToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>'; // Icône pour le bouton
    scrollToTopBtn.id = 'scrollToTopBtn'; // ID pour le ciblage CSS
    scrollToTopBtn.setAttribute('aria-label', 'Remonter en haut de la page'); // Accessibilité
    document.body.appendChild(scrollToTopBtn); // Ajout du bouton au corps du document

    const toggleScrollToTopButton = () => {
        if (window.pageYOffset > 200) { // Afficher le bouton si le défilement dépasse 200px
            scrollToTopBtn.classList.add('show');
        } else { // Cacher le bouton sinon
            scrollToTopBtn.classList.remove('show');
        }
    };

    window.addEventListener('scroll', toggleScrollToTopButton); // Écouter l'événement de défilement
    scrollToTopBtn.addEventListener('click', () => { // Action au clic sur le bouton
        window.scrollTo({ top: 0, behavior: 'smooth' }); // Défilement doux vers le haut
    });

    // Vérifier l'état initial au chargement de la page
    toggleScrollToTopButton();

});
