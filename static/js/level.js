const btn = document.getElementById('btn-level-up');
if (btn) {
    btn.addEventListener('click', () => {
        btn.disabled = true;
        fetch('/api/level-up', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    btn.textContent = '✅ Niveau atteint !';
                    setTimeout(() => btn.remove(), 2000);
                } else {
                    btn.disabled = false;
                }
            });
    });
}