const input    = document.getElementById('search-input');
const clearBtn = document.getElementById('search-clear');
const form     = document.getElementById('search-form');

if (input && clearBtn) {
    function updateClear() {
        clearBtn.style.display = input.value ? 'flex' : 'none';
    }
    clearBtn.addEventListener('click', () => {
        input.value = '';
        clearBtn.style.display = 'none';
        if (form) form.submit();
    });
    input.addEventListener('input', updateClear);
    updateClear();
}
