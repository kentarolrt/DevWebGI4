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

const photoInput = document.getElementById('photo-input');
if (photoInput) {
    photoInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('photo', file);
        const response = await fetch('/profile/photo', { method: 'POST', body: formData });
        const result = await response.json();
        if (result.ok) {
            const container = document.getElementById('avatar-container');
            let img = container.querySelector('img');
            if (!img) {
                img = document.createElement('img');
                img.className = 'profile-avatar-img';
                img.alt = 'Photo de profil';
                container.querySelector('#avatar-initial')?.remove();
                container.insertBefore(img, container.querySelector('.avatar-upload-overlay'));
            }
            img.src = '/static/uploads/photos/' + result.filename + '?t=' + Date.now();
        } else {
            alert('Erreur lors de l\'upload : ' + (result.error || 'inconnue'));
        }
        photoInput.value = '';
    });
}

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

const PW_ERRORS = {
    mismatch:      'Les mots de passe ne correspondent pas.',
    wrong_password:'Mot de passe actuel incorrect.',
    too_short:     'Le nouveau mot de passe doit faire au moins 6 caractères.',
};

function enableEdit(btn) {
    btn.textContent = 'Modifier';
    btn.onclick = () => {
        const field = btn.dataset.field;
        const valueSpan = document.getElementById(field);

        if (field === 'password') {
            const wrap = document.createElement('div');
            wrap.className = 'password-edit-wrap';
            ['Mot de passe actuel', 'Nouveau mot de passe', 'Confirmer'].forEach(ph => {
                const inp = document.createElement('input');
                inp.type = 'password';
                inp.placeholder = ph;
                wrap.appendChild(inp);
            });
            const saveBtn = document.createElement('button');
            saveBtn.className = 'btn-save-password';
            saveBtn.type = 'button';
            saveBtn.textContent = 'Enregistrer';
            wrap.appendChild(saveBtn);
            valueSpan.replaceWith(wrap);
            btn.closest('.profile-field').classList.add('profile-field--pw-editing');
            wrap.querySelector('input').focus();

            btn.textContent = 'Annuler';
            btn.onclick = () => {
                const newSpan = document.createElement('span');
                newSpan.className = 'profile-field-value';
                newSpan.id = 'password';
                newSpan.textContent = '••••••••';
                wrap.replaceWith(newSpan);
                btn.closest('.profile-field').classList.remove('profile-field--pw-editing');
                enableEdit(btn);
            };

            saveBtn.onclick = async () => {
                const inputs = [...wrap.querySelectorAll('input')];
                const [current, newPw, confirm] = inputs.map(i => i.value);
                if (!current || !newPw || !confirm) { alert('Veuillez remplir tous les champs.'); return; }
                const resp = await fetch('/profile/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ current_password: current, new_password: newPw, confirm_password: confirm })
                });
                const result = await resp.json();
                if (result.ok) {
                    const newSpan = document.createElement('span');
                    newSpan.className = 'profile-field-value';
                    newSpan.id = 'password';
                    newSpan.textContent = '••••••••';
                    wrap.replaceWith(newSpan);
                    btn.closest('.profile-field').classList.remove('profile-field--pw-editing');
                    enableEdit(btn);
                } else {
                    alert(PW_ERRORS[result.error] || 'Erreur : ' + result.error);
                }
            };
            return;
        }

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
