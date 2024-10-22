//hide preloader
window.addEventListener('load', (e) => {
	var preloader = document.getElementById('pre-loader')
	setTimeout(() => {
		preloader.style.display = 'none'
	},700)
})