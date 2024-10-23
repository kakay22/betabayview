
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    const repairmanCards = document.querySelectorAll('#repairmanContainer #repairman');

    searchInput.addEventListener('input', function () {
        const query = searchInput.value.toLowerCase();

        repairmanCards.forEach(card => {
            const name = card.querySelector('h2').textContent.toLowerCase();
            const role = card.querySelector('span').textContent.toLowerCase();
            const location = card.querySelector('.bi-geo-alt-fill + span').textContent.toLowerCase();

            if (name.includes(query) || role.includes(query) || location.includes(query)) {
                card.style.display = ''; // Show card
            } else {
                card.style.display = 'none'; // Hide card
            }
        });
    });
});
