document.addEventListener('DOMContentLoaded', () => {
    const clickableCards = document.querySelectorAll('.card[data-modal-id]');
    
    clickableCards.forEach(card => {
        card.addEventListener('click', () => {
            const modalId = card.getAttribute('data-modal-id');
            const modal = document.getElementById(modalId);

            if (modal) {
                // Get data from attributes
                const title = card.getAttribute('data-title');
                const imageUrl = card.getAttribute('data-image');
                const date = card.getAttribute('data-date');
                
                // Get full content from the hidden div - THIS IS THE FIX
                const contentElement = card.querySelector('.full-content');
                const content = contentElement ? contentElement.innerHTML : 'Conteúdo não encontrado.';
                
                // Populate modal
                modal.querySelector('.modal-title').textContent = title;
                modal.querySelector('.modal-body .modal-text-content').innerHTML = content;
                modal.querySelector('.modal-date').textContent = date;

                const imageElement = modal.querySelector('.modal-body img');
                if (imageUrl && imageUrl !== 'None') {
                    imageElement.src = imageUrl;
                    imageElement.alt = title; // Good practice to set alt text
                    imageElement.style.display = 'block';
                } else {
                    imageElement.style.display = 'none';
                }

                modal.style.display = 'block';
            }
        });
    });

    // Close buttons logic (remains the same)
    const closeButtons = document.querySelectorAll('.close-button');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.modal').style.display = 'none';
        });
    });

    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });
});