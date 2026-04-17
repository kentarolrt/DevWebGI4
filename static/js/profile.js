document.querySelectorAll('.btn-edit').forEach(btn => {
    enableEdit(btn)
})

function enableEdit(btn) {
    btn.textContent = 'modifier'
    btn.onclick = () => {
        const field = btn.dataset.field
        const valueSpan = document.getElementById(field)
        const currentValue = valueSpan.textContent

        const input = document.createElement('input')
        input.type = 'text'
        input.value = currentValue
        valueSpan.replaceWith(input)
        input.focus()

        btn.textContent = 'annuler'
        btn.onclick = () => {
            const newSpan = document.createElement('span')
            newSpan.className = 'value'
            newSpan.id = field
            newSpan.textContent = currentValue
            input.replaceWith(newSpan)
            enableEdit(btn)
        }

        input.addEventListener('keydown', async (e) => {
            if (e.key !== 'Enter') return
            const newValue = input.value.trim()
            if (!newValue) return

            const response = await fetch('/profile/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field, value: newValue })
            })

            const result = await response.json()

            if (result.ok) {
                const newSpan = document.createElement('span')
                newSpan.className = 'value'
                newSpan.id = field
                newSpan.textContent = newValue
                input.replaceWith(newSpan)
                enableEdit(btn)
            } else {
                alert(result.error)
            }
        })
    }
}