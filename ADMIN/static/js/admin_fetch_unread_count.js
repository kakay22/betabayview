//fetch unread notification
function fetchUnreadCount() {
	fetch("{% url 'admin_unread_notifications_count' %}")
		.then(response => response.json())
		.then(data => {
				const notificationCount = data.unread_count;
				const notificationBadge = document.querySelector('.notification-badge');
				if (notificationCount > 0) {
					notificationBadge.textContent = notificationCount;
					notificationBadge.classList.remove('hidden'); // Show badge
				} else {
					notificationBadge.classList.add('hidden'); // Hide badge
				}
			});
	}
	// Call this function to check unread notifications every .5 second
	setInterval(fetchUnreadCount, 500);
	fetchUnreadCount();  // Initial call to set the count immediately