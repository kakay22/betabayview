searchValue = document.getElementById('searchInput')

searchValue.addEventListener('keyup', (e) => {
	var rows = document.querySelectorAll('#myTable tbody tr')

	rows.forEach((row) => {
		const cells = row.querySelectorAll('td')
		let rowText = ''

		cells.forEach((cell) => {
			rowText += cell.textContent.toLowerCase();
		});

		if (rowText.includes(searchValue.value)) {
			row.style.display = ''
		} else {
			row.style.display = 'none'
		}
	})
})