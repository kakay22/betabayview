$(document).ready(function() {
    function fetchMessages() {
        $.ajax({
            url: '{% url "get_new_messages" %}',
            method: 'GET',
            success: function(data) {
                if (data.length > 0) {
                    $('#message-indicator').show(); // Show the red dot indicator
                } else {
                    $('#message-indicator').hide(); // Hide the red dot indicator
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error fetching messages:', textStatus, errorThrown);
            }
        });
    }

    // Polling every 5 seconds
    setInterval(fetchMessages, 1000);

    // Mark messages as read and navigate to messages page
    $('#message-button').click(function() {
        $.ajax({
            url: '{% url "mark_messages_as_read" %}',
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}'
            },
            success: function(data) {
                if (data.status === 'ok') {
                    $('#message-indicator').hide(); // Hide the red dot indicator
                    window.location.href = '{% url "owner_messages" %}'; // Redirect to messages page
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error marking messages as read:', textStatus, errorThrown);
            }
        });
    });
});