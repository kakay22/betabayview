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
