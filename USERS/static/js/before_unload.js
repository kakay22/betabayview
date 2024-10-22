//hide preloader
window.addEventListener('beforeunload', (e) => {
	var preloader = document.getElementById('pre-loader')
	preloader.style.display = 'flex'
})