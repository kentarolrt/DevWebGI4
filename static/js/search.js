const input = document.getElementById('search-input');
const clearBtn = document.getElementById('search-clear');
const form = document.getElementById('search-form');

function updateClear() {
    const isMobile = window.innerWidth <= 768;
    clearBtn.style.display = (!isMobile && input.value) ? 'flex' : 'none';
}

clearBtn.addEventListener('click', () => {
    input.value = '';
    form.submit();
});

input.addEventListener('input', updateClear);
updateClear();
