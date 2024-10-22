searchValue = document.getElementById('searchInput')

searchValue.addEventListener('keyup', (e) => {
	var rows = document.querySelectorAll('#myTable tbody tr')
	var noResultsFound = document.getElementById('noResultsFound'); // Reference to "No results found" message
	var matchFound = false // Track if any match is found

	rows.forEach((row) => {
		const cells = row.querySelectorAll('td')
		let rowText = ''

		cells.forEach((cell) => {
			rowText += cell.textContent.toLowerCase();
		});

		if (rowText.includes(searchValue.value.toLowerCase())) {
			row.style.display = ''
			matchFound = true // A match is found
		} else {
			row.style.display = 'none'
		}
	})

	// Check if no matches were found
	if (!matchFound && input !== '') {
		noResultsFound.style.display = 'block'; // Show "No results found" message
	} else {
		noResultsFound.style = 'none'; // Hide the message if results found
	}
})


$(document).ready(function() {
    function filterTable() {
        // Get the selected values from the filters
        var selectedGender = $('#gender').val().toLowerCase();
        var selectedRelationship = $('#relationship').val().toLowerCase();

        // Filter table rows
        $('#myTable tbody tr').filter(function() {
            var genderText = $(this).find('td:nth-child(2)').text().toLowerCase(); // Adjust based on column index
            var relationshipText = $(this).find('td:nth-child(3)').text().toLowerCase(); // Adjust based on column index

            // Check if the row matches the selected values
            var matchGender = selectedGender ? genderText.includes(selectedGender) : true;
            var matchRelationship = selectedRelationship ? relationshipText.includes(selectedRelationship) : true;

            // Show or hide the row based on the filters
            $(this).toggle(matchGender && matchRelationship);
        });
    }

    // Event listeners for the filters
    $('#gender, #relationship').on('change', filterTable);
});
