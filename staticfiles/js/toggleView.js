const listViewBtn = document.querySelector("#listViewBtn")
const gridViewBtn = document.querySelector("#gridViewBtn")
const listView = document.querySelector("#listView")
const gridView = document.querySelector("#gridView")

gridViewBtn.addEventListener('click', (e) => {
	listView.style.display = 'none'
	gridView.style.display = 'block'

	listViewBtn.style.display = 'block'
	gridViewBtn.style.display = 'none'
})

listViewBtn.addEventListener('click', (e) => {
	listView.style.display = 'block'
	gridView.style.display = 'none'

	listViewBtn.style.display = 'none'
	gridViewBtn.style.display = 'block'
})