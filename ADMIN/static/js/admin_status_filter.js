document.addEventListener('DOMContentLoaded', function() {
    // Get references to the filter dropdown, table rows, and grid view cards
    const filterDropdown = document.getElementById('filterCriteria');
    const tableRows = document.querySelectorAll('#homeownersTable tr');
    const gridViewCards = document.querySelectorAll('#gridView .property-card'); // Class to target grid cards

    // Add event listener for when the user changes the dropdown
    filterDropdown.addEventListener('change', function() {
        const filterValue = filterDropdown.value.toLowerCase(); // Get the selected filter value (occupied/available)

        // Loop through all table rows and filter based on the status column
        tableRows.forEach(row => {
            const statusCell = row.querySelector('td:nth-child(10) p'); // The status is in the 10th cell with a <p> tag
            if (statusCell) {
                const statusText = statusCell.textContent.trim().toLowerCase(); // Get status text from the <p> tag
                if (filterValue === "" || filterValue === "all" || statusText.includes(filterValue)) {
                    row.style.display = ""; // Show row if status matches filter
                } else {
                    row.style.display = "none"; // Hide row if status doesn't match filter
                }
            }
        });

        // Loop through all grid view cards and filter based on the status
        gridViewCards.forEach(card => {
            const statusTag = card.querySelector('.availability-status'); // The status class in grid view cards
            if (statusTag) {
                const statusText = statusTag.textContent.trim().toLowerCase();
                if (filterValue === "" || statusText.includes(filterValue)) {
                    card.style.display = ""; // Show card if status matches filter
                } else {
                    card.style.display = "none"; // Hide card if status doesn't match filter
                }
            }
        });
    });
});
