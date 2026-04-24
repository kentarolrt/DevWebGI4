const deviceId = document.getElementById('device-id').value;
const msg = document.getElementById('points-msg');

if (msg) {
    fetch('/api/consult/' + deviceId, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                msg.textContent = '+0.50 pts crédités ✅ — Total : ' + data.points.toFixed(2) + ' pts';
            } else {
                msg.textContent = '';
            }
        });
}