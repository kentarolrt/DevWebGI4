document.querySelectorAll('.btn-field-edit').forEach(btn => {
    enableEdit(btn);
});

function enableEdit(btn) {
    btn.textContent = 'Modifier';
    btn.onclick = () => {
        const field = btn.dataset.field;
        const valueSpan = document.getElementById(field);
        const currentValue = valueSpan.textContent.trim() === '—' ? '' : valueSpan.textContent.trim();

        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentValue;
        valueSpan.replaceWith(input);
        input.focus();

        btn.textContent = 'Annuler';
        btn.onclick = () => {
            const newSpan = document.createElement('span');
            newSpan.className = 'profile-field-value';
            newSpan.id = field;
            newSpan.textContent = currentValue || '—';
            input.replaceWith(newSpan);
            enableEdit(btn);
        };

        input.addEventListener('keydown', async (e) => {
            if (e.key !== 'Enter') return;
            const newValue = input.value.trim();
            if (!newValue) return;

            const response = await fetch('/profile/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field, value: newValue })
            });

            const result = await response.json();

            if (result.ok) {
                const newSpan = document.createElement('span');
                newSpan.className = 'profile-field-value';
                newSpan.id = field;
                newSpan.textContent = newValue;
                input.replaceWith(newSpan);
                if (field === 'username') {
                    document.querySelector('.profile-username').textContent = newValue;
                    document.querySelector('.btn-profile').textContent = newValue;
                }
                enableEdit(btn);
            } else {
                alert('Erreur : ' + (result.error || 'inconnue'));
                input.focus();
            }
        });
    };
}
