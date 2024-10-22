function initMap() {
	if (document.getElementById('map').children.length > 0) return;

	const map = L.map('map').setView([11.2405, 125.0034], 16); // Coordinates for Pope Francis Village

	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		maxZoom: 19,
	}).addTo(map);

	const geocoder = L.Control.Geocoder.nominatim();
	const control = L.Control.geocoder({
		query: '',
		placeholder: 'Search for a place...',
		defaultMarkGeocode: true,
		geocoder
	}).on('markgeocode', function (e) {
		const latlng = e.geocode.center;
		L.marker(latlng).addTo(map).bindPopup(e.geocode.name).openPopup();
		map.setView(latlng, 16);

		// Show message to tap on blocks only if near Pope Francis Village
		const distanceToPFV = map.distance(latlng, [11.2405, 125.0034]);
		if (distanceToPFV < 600) { // 600 meters (adjust as needed)
			mapMessage.style.display = 'block';
		} else {
			mapMessage.style.display = 'none';
		}
	}).addTo(map);

	let lat, lng; // Define lat and lng variables

	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(position => {
			lat = position.coords.latitude;
			lng = position.coords.longitude;
			const currentLocation = L.marker([lat, lng]).addTo(map).bindPopup('Your current location').openPopup();
			map.setView([lat, lng], 16);

			control.on('markgeocode', function (e) {
				const latlng = e.geocode.center;
				L.Routing.control({
					waypoints: [
						L.latLng(lat, lng),
						L.latLng(latlng.lat, latlng.lng)
					],
					createMarker: function (i, wp) {
						return L.marker(wp.latLng).bindPopup(i === 0 ? 'Start' : 'End').openPopup();
					},
					routeWhileDragging: true, // Enable dragging of route points
					geocoder: geocoder
				}).addTo(map);
			});
		});
	} else {
		alert('Geolocation is not supported by this browser.');
	}

	// Button to navigate to Pope Francis Village
	const navigateBtn = document.createElement('button');
	navigateBtn.classList.add('absolute', 'bottom-2', 'left-2', 'flex', 'items-center', 'z-[999]', 'bg-white', 'border', 'border-gray-300', 'px-2.5', 'py-1', 'rounded', 'cursor-pointer', 'shadow-md', 'hover:bg-gray-100');
	navigateBtn.innerHTML = 'Navigate to Pope Francis Village<i class="bi bi-arrow-up-right text-[1.5rem] ml-1"></i>';
	navigateBtn.addEventListener('click', () => {
		const query = 'Pope Francis Village, Tacloban'; // Query string for geocoder
		geocoder.geocode(query, results => {
			if (results.length > 0) {
				const latlng = results[0].center;
				map.setView(latlng, 16); // Center on Pope Francis Village
				L.Routing.control({
					waypoints: [
						L.latLng(lat, lng),
						L.latLng(latlng.lat, latlng.lng)
					],
					createMarker: function (i, wp) {
						return L.marker(wp.latLng).bindPopup(i === 0 ? 'Start' : 'End').openPopup();
					},
					routeWhileDragging: true, // Enable dragging of route points
					geocoder: geocoder
				}).addTo(map);
			} else {
				console.log('Location not found');
			}
		});
	});
	mapContainer.appendChild(navigateBtn);
}