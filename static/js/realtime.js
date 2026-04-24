const socket = io();

socket.on('connect', () => {
    socket.emit('join');
});

const LEVEL_LABELS = {
    debutant: 'Débutant',
    intermediaire: 'Intermédiaire',
    avance: 'Avancé',
    expert: 'Expert'
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
    }
});