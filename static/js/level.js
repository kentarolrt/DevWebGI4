const LEVEL_LABELS = {
    debutant:      'Débutant',
    intermediaire: 'Intermédiaire',
    avance:        'Avancé',
    expert:        'Expert'
};

const LEVEL_NEXT = {
    debutant:      { next_label: 'Intermédiaire', next_pts: 1, min: 0 },
    intermediaire: { next_label: 'Avancé',        next_pts: 3, min: 1 },
    avance:        { next_label: 'Expert',         next_pts: 5, min: 3 },
    expert:        null
};

function updateDashboardLevel(level, points) {
    const label = LEVEL_LABELS[level] || level;

    document.querySelectorAll('.level-live').forEach(el => { el.textContent = label; });

    const welcomeP = document.querySelector('.dash-welcome-text p');
    if (welcomeP) welcomeP.innerHTML = `Niveau actuel : <strong>${label}</strong>`;

    const card = document.querySelector('.dash-progress-card');
    if (!card) return;

    card.dataset.level = level;

    const info = LEVEL_NEXT[level];
    if (!info) {
        card.innerHTML = `<div class="dash-progress-header">
            <span><i class="fa-solid fa-star"></i> Vous avez atteint le niveau maximum : <strong>Expert</strong></span>
        </div>`;
        return;
    }

    const range = info.next_pts - info.min;
    const pct = Math.min(100, Math.max(0, Math.round((points - info.min) / range * 100)));
    const canLevelUp = points >= info.next_pts;

    card.innerHTML = `
        <div class="dash-progress-header">
            <span>Progression vers <strong>${info.next_label}</strong></span>
            <span class="dash-progress-pts"><span class="points-live">${points.toFixed(2)}</span> / ${info.next_pts} pts</span>
        </div>
        <div class="dash-progress-bar" data-progress="${pct}">
            <div class="dash-progress-fill" style="width:${pct}%"></div>
        </div>
        ${canLevelUp
            ? `<button class="btn-level-up" id="btn-level-up"><i class="fa-solid fa-trophy"></i> Passer au niveau ${info.next_label}</button>`
            : `<p class="dash-progress-hint">Il vous manque <strong>${(info.next_pts - points).toFixed(2)} pts</strong> pour passer au niveau suivant.</p>`
        }`;

    const newBtn = document.getElementById('btn-level-up');
    if (newBtn) bindLevelUp(newBtn);
}

function bindLevelUp(btn) {
    btn.addEventListener('click', () => {
        btn.disabled = true;
        fetch('/api/level-up', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Niveau atteint !';
                    setTimeout(() => location.reload(), 1200);
                } else {
                    btn.disabled = false;
                }
            });
    });
}

const btn = document.getElementById('btn-level-up');
if (btn) bindLevelUp(btn);
