const FIELD_SELECTS = {
    gender: [
        { value: 'male',   label: 'Homme' },
        { value: 'female', label: 'Femme' },
        { value: 'other',  label: 'Autre' },
    ],
    member_type: [
        { value: 'père',  label: 'Père' },
        { value: 'mère',  label: 'Mère' },
        { value: 'fils',  label: 'Fils' },
        { value: 'fille', label: 'Fille' },
    ],
};

const FIELD_TYPES = {
    age:       'number',
    birthdate: 'date',
};

document.querySelectorAll('.btn-field-edit').forEach(btn => {
    enableEdit(btn);
});

function getDisplayLabel(field, value) {
    if (!value) return '—';
    const opts = FIELD_SELECTS[field];
    if (opts) {
        const opt = opts.find(o => o.value === value);
        return opt ? opt.label : value;
    }
    return value;
}

function createInput(field, currentValue) {
    const opts = FIELD_SELECTS[field];
    if (opts) {
        const sel = document.createElement('select');
        sel.className = 'profile-inline-select';
        opts.forEach(o => {
            const opt = document.createElement('option');
            opt.value = o.value;
            opt.textContent = o.label;
            if (o.value === currentValue) opt.selected = true;
            sel.appendChild(opt);
        });
        return sel;
    }

    const input = document.createElement('input');
    input.type = FIELD_TYPES[field] || 'text';
    input.value = currentValue;
    return input;
}

function enableEdit(btn) {
    btn.textContent = 'Modifier';
    btn.onclick = () => {
        const field = btn.dataset.field;
        const valueSpan = document.getElementById(field);
        const currentValue = valueSpan.dataset.value !== undefined
            ? valueSpan.dataset.value
            : (valueSpan.textContent.trim() === '—' ? '' : valueSpan.textContent.trim());

        const control = createInput(field, currentValue);
        valueSpan.replaceWith(control);
        if (control.focus) control.focus();

        btn.textContent = 'Annuler';
        btn.onclick = () => {
            const newSpan = makeSpan(field, currentValue);
            control.replaceWith(newSpan);
            enableEdit(btn);
        };

        const save = async () => {
            const newValue = control.tagName === 'SELECT' ? control.value : control.value.trim();
            if (!newValue) return;

            const response = await fetch('/profile/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field, value: newValue })
            });
            const result = await response.json();

            if (result.ok) {
                const newSpan = makeSpan(field, newValue);
                control.replaceWith(newSpan);
                if (field === 'username') {
                    document.querySelector('.profile-username').textContent = newValue;
                    document.querySelector('.btn-profile').textContent = newValue;
                }
                enableEdit(btn);
            } else {
                alert('Erreur : ' + (result.error || 'inconnue'));
                if (control.focus) control.focus();
            }
        };

        if (control.tagName === 'SELECT') {
            btn.textContent = 'Enregistrer';
            btn.onclick = async () => {
                await save();
            };
        } else {
            control.addEventListener('keydown', async (e) => {
                if (e.key === 'Enter') await save();
            });
        }
    };
}

function makeSpan(field, value) {
    const span = document.createElement('span');
    span.className = 'profile-field-value';
    span.id = field;
    span.dataset.value = value;
    span.textContent = getDisplayLabel(field, value) || value || '—';
    return span;
}
