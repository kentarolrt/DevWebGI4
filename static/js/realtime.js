const socket = io();

socket.on('connect', () => {
    socket.emit('join');
});

const LEVEL_LABELS = {
    debutant:      'Débutant',
    intermediaire: 'Intermédiaire',
    avance:        'Avancé',
    expert:        'Expert'
};

const LEVEL_NEXT = {
    debutant:      { next_label: 'Intermédiaire', next_pts: 5,  min: 0  },
    intermediaire: { next_label: 'Avancé',        next_pts: 15, min: 5  },
    avance:        { next_label: 'Expert',        next_pts: 30, min: 15 },
};

socket.on('points_update', (data) => {
    document.querySelectorAll('.points-live').forEach(el => {
        el.textContent = data.points.toFixed(2);
    });

    if (data.level) {
        const label = LEVEL_LABELS[data.level] || data.level;
        document.querySelectorAll('.level-live').forEach(el => {
            el.textContent = label;
        });
        if (typeof updateDashboardLevel === 'function') {
            updateDashboardLevel(data.level, data.points);
        }
    } else {
        _syncProgressCard(data.points);
    }
});

function _syncProgressCard(points) {
    const card = document.querySelector('.dash-progress-card');
    if (!card || !card.dataset.level) return;

    const level = card.dataset.level;
    const info = LEVEL_NEXT[level];
    if (!info) return;

    const range = info.next_pts - info.min;
    const pct = Math.min(100, Math.max(0, Math.round((points - info.min) / range * 100)));

    const fill = card.querySelector('.dash-progress-fill');
    if (fill) fill.style.width = pct + '%';

    const hint = card.querySelector('.dash-progress-hint');
    if (hint && points >= info.next_pts) {
        hint.outerHTML = `<button class="btn-level-up" id="btn-level-up"><i class="fa-solid fa-trophy"></i> Passer au niveau ${info.next_label}</button>`;
        const newBtn = document.getElementById('btn-level-up');
        if (newBtn && typeof bindLevelUp === 'function') bindLevelUp(newBtn);
    }
}
