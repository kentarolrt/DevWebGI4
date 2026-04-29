const bar = document.querySelector('.dash-progress-bar');
if (bar) {
    const fill = bar.querySelector('.dash-progress-fill');
    fill.style.width = bar.dataset.progress + '%';
}

function refreshPoints() {
    fetch('/api/points')
        .then(r => r.json())
        .then(data => {
            if (!data.ok) return;
            document.querySelectorAll('.points-live').forEach(el => {
                el.textContent = data.points.toFixed(2);
            });
            if (typeof updateDashboardLevel === 'function') {
                updateDashboardLevel(data.level, data.points);
            }
        });
}

window.addEventListener('pageshow', (e) => {
    if (e.persisted) refreshPoints();
});