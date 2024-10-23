// Search input element
const searchValue = document.getElementById('searchInput');

// Add an event listener for the 'keyup' event
searchValue.addEventListener('keyup', (e) => {
    const searchQuery = searchValue.value.toLowerCase();
    
    // Get table rows and property cards
    const rows = document.querySelectorAll('#myTable tbody tr');
    const propertyCards = document.querySelectorAll('.property-card');

    let matchFound = false; // Track if any match is found in table or grid
    const noResultsFound = document.getElementById('noResultsFound'); // "No results found" message

    // Filter rows in the table view
    rows.forEach((row) => {
        const rowText = row.innerText.toLowerCase();
        if (rowText.includes(searchQuery)) {
            row.style.display = ''; // Show matching row
            matchFound = true; // Mark that a match is found
        } else {
            row.style.display = 'none'; // Hide non-matching row
        }
    });

    // Filter property cards in the grid view
    propertyCards.forEach((card) => {
        const cardText = card.innerText.toLowerCase();
        if (cardText.includes(searchQuery)) {
            card.style.display = ''; // Show matching card
            matchFound = true; // Mark that a match is found
        } else {
            card.style.display = 'none'; // Hide non-matching card
        }
    });

    // Display or hide the "No results found" message
    if (!matchFound) {
        noResultsFound.style.display = 'block'; // Show "No results found" message
    } else {
        noResultsFound.style.display = 'none'; // Hide the message if results are found
    }
});
