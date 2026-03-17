// Responsive behavior enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Handle responsive tables
    makeTablesResponsive();

    // Handle responsive cards
    makeCardsResponsive();

    // Handle responsive charts
    makeChartsResponsive();

    // Handle orientation change
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            makeChartsResponsive();
        }, 200);
    });

    // Handle resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            makeChartsResponsive();
            adjustSidebarForScreen();
        }, 250);
    });
});

function makeTablesResponsive() {
    const tables = document.querySelectorAll('.table:not(.table-responsive table)');
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

function makeCardsResponsive() {
    const cardHeaders = document.querySelectorAll('.card-header');
    cardHeaders.forEach(header => {
        if (!header.classList.contains('card-header-responsive')) {
            const actions = header.querySelector('.btn-group, .btn, .dropdown');
            if (actions && header.children.length > 1) {
                header.classList.add('card-header-responsive');
            }
        }
    });
}

function makeChartsResponsive() {
    const charts = document.querySelectorAll('.chart-container canvas');
    charts.forEach(canvas => {
        if (canvas.chart) {
            canvas.chart.resize();
        }
    });
}

function adjustSidebarForScreen() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    if (!sidebar || !mainContent) return;

    if (window.innerWidth <= 768) {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('expanded');
    } else {
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
    }
}

// Handle touch events for mobile
if ('ontouchstart' in window) {
    document.addEventListener('touchstart', handleTouch, { passive: true });

    let touchStartX = 0;
    let touchEndX = 0;

    function handleTouch(event) {
        touchStartX = event.touches[0].clientX;
    }

    document.addEventListener('touchend', function(event) {
        touchEndX = event.changedTouches[0].clientX;
        handleSwipe();
    }, { passive: true });

    function handleSwipe() {
        const sidebar = document.getElementById('sidebar');
        const swipeThreshold = 50;

        if (!sidebar) return;

        // Swipe right to open sidebar on mobile
        if (touchEndX - touchStartX > swipeThreshold && window.innerWidth <= 768) {
            sidebar.classList.add('mobile-show');
            const toggle = document.getElementById('mobileSidebarToggle');
            if (toggle) toggle.innerHTML = '<i class="fas fa-times"></i>';
        }

        // Swipe left to close sidebar on mobile
        if (touchStartX - touchEndX > swipeThreshold && window.innerWidth <= 768) {
            sidebar.classList.remove('mobile-show');
            const toggle = document.getElementById('mobileSidebarToggle');
            if (toggle) toggle.innerHTML = '<i class="fas fa-bars"></i>';
        }
    }
}