// LocalStorage key for storing search history
const searchHistoryKey = 'searchHistory'; 

// Event listener for the search button
const searchButton = document.getElementById('search-button');

searchButton.addEventListener('click', function (event) {
    event.preventDefault(); // Prevent any default action
    const searchInput = document.getElementById('search-input');

    searchButton.classList.add('bg-transparent');
    searchButton.classList.add('z-[1099]');

    // Expand the input and show the button
    searchInput.classList.add('expanded');

    // Show the suggestions dropdown when the input is focused
    searchInput.focus();

    // Load and display search history
    loadSearchHistory();
    const suggestionsDropdown = document.getElementById('suggestions-dropdown');
    suggestionsDropdown.style.display = 'block'; // Show suggestions dropdown
});

// Collapse the search bar when it loses focus (blur event)
document.getElementById('search-input').addEventListener('blur', function () {
    const searchInput = this;
    const suggestionsDropdown = document.getElementById('suggestions-dropdown');

    // Delay hiding the dropdown to allow click event on suggestions or history items
    setTimeout(() => {
        if (!document.activeElement.closest('.history-item') && !document.activeElement.closest('.delete-history-item')) {
            searchButton.classList.remove('bg-transparent');
            searchInput.classList.remove('expanded');
            searchButton.classList.remove('z-[1099]');
            suggestionsDropdown.style.display = 'none';
        }
    }, 200); // Delay to allow interaction with history items
});

// Collapse the search bar if clicked outside (click event)
document.addEventListener('click', function (event) {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const suggestionsDropdown = document.getElementById('suggestions-dropdown');

    // Check if the click happened outside the search input, button, and dropdown
    if (!searchInput.contains(event.target) && !searchButton.contains(event.target) && !suggestionsDropdown.contains(event.target)) {
        // Collapse the input and hide the suggestions dropdown
        searchButton.classList.remove('bg-transparent');
        searchInput.classList.remove('expanded');
        searchButton.classList.remove('z-[1099]');
        suggestionsDropdown.style.display = 'none'; // Hide suggestions dropdown
    }
});

// Update the suggestions based on input
document.getElementById('search-input').addEventListener('input', function () {
    const inputText = this.value.toLowerCase();
    const suggestionsDropdown = document.getElementById('suggestions-dropdown');

    // Reference to the searchSuggestionsElement (from dataset attributes)
    const searchSuggestionsElement = document.getElementById('search-suggestions'); // Assuming this is the correct element

    // List of suggestions with corresponding URLs
    const suggestions = [
        { name: 'Dashboard', url: searchSuggestionsElement.dataset.dashboardUrl },
        { name: 'Profile setting', url: searchSuggestionsElement.dataset.profileUrl },
        { name: 'Property details', url: searchSuggestionsElement.dataset.propertyDetailsUrl },
        { name: 'Household members', url: searchSuggestionsElement.dataset.householdMembersUrl },
        { name: 'Maintenance', url: searchSuggestionsElement.dataset.maintenanceUrl },
        { name: 'Events', url: searchSuggestionsElement.dataset.eventsUrl },
        { name: 'Announcements', url: searchSuggestionsElement.dataset.announcementsUrl },
        { name: 'Notifications', url: searchSuggestionsElement.dataset.notificationsUrl }
    ];

    // Clear previous suggestions
    suggestionsDropdown.innerHTML = '';

    // Filter and show matching suggestions
    if (inputText) {
        const filteredSuggestions = suggestions.filter(suggestion => 
            suggestion.name.toLowerCase().includes(inputText)
        );
        
        // Check if there are any matching suggestions
        if (filteredSuggestions.length > 0) {
            filteredSuggestions.forEach(suggestion => {
                // Create a regular expression to match the input text
                const regex = new RegExp(`(${inputText})`, 'gi');
                // Create a new element to show the suggestion with highlighted matching text
                const suggestionElement = document.createElement('div');
                suggestionElement.innerHTML = suggestion.name.replace(regex, '<span class="highlight">$1</span>'); // Highlight matching text
                suggestionElement.classList.add('p-2', 'cursor-pointer', 'hover:bg-gray-200');

                // Add event listener for redirecting on click
                suggestionElement.addEventListener('mousedown', function () {
                    window.location.href = suggestion.url; // Redirect to the selected suggestion's URL
                    saveSearchHistory(suggestion.name); // Save to search history
                });

                suggestionsDropdown.appendChild(suggestionElement);
            });
        } else {
            // Display "No results found" message with an icon
            const noResultsElement = document.createElement('div');
            noResultsElement.classList.add('p-2', 'text-gray-500', 'flex', 'items-center');
            noResultsElement.innerHTML = `
                <span class="material-icons mr-2">warning</span>
                No results found
            `;
            suggestionsDropdown.appendChild(noResultsElement);
        }
        
        // Show suggestions dropdown
        suggestionsDropdown.style.display = 'block';
    } else {
        loadSearchHistory(); // Show search history when input is empty
    }
});

// Prevent the search input from collapsing when clicking inside the suggestions dropdown
document.getElementById('suggestions-dropdown').addEventListener('mousedown', function(event) {
    event.preventDefault(); // Prevent blur and collapse when clicking on suggestions
});

// Save search to history
function saveSearchHistory(searchTerm) {
    let history = JSON.parse(localStorage.getItem(searchHistoryKey)) || [];
    // Add new search to history if it doesn't already exist
    if (!history.includes(searchTerm)) {
        history.push(searchTerm);
    }
    localStorage.setItem(searchHistoryKey, JSON.stringify(history));
    loadSearchHistory();
}

// Load search history
function loadSearchHistory() {
    const suggestionsDropdown = document.getElementById('suggestions-dropdown');
    const searchHistoryContainer = document.createElement('div'); // Container for history
    searchHistoryContainer.classList.add('search-history-container', 'border-t', 'pt-2');

    let history = JSON.parse(localStorage.getItem(searchHistoryKey)) || [];

    // Clear the suggestionsDropdown for showing history
    suggestionsDropdown.innerHTML = '';

    // Add history items to the dropdown
    if (history.length > 0) {
        history.forEach(term => {
            // Check if the term is a valid string
            if (typeof term === 'string' && term.trim() !== '') {
                const historyItem = document.createElement('div');
                historyItem.classList.add('history-item', 'p-2', 'flex', 'justify-between', 'hover:bg-gray-200', 'cursor-pointer');

                // Create a span for the term text
                const termText = document.createElement('span');
                termText.textContent = term;
                termText.classList.add('flex-1', 'text-left');

                // Create delete button
                const deleteButton = document.createElement('a');
                deleteButton.classList.add('bi', 'bi-x', 'delete-history-item', 'px-2', 'p-1', 'hover:bg-gray-300', 'rounded-md');

                // Add click event to the history item to redirect
                historyItem.addEventListener('click', function () {
                    const suggestion = suggestions.find(s => s.name.toLowerCase() === term.toLowerCase());
                    if (suggestion) {
                        // Redirect to the appropriate URL if a match is found
                        window.location.href = suggestion.url;
                    } else {
                        // If no match, you can handle it accordingly (e.g., perform a search)
                        const searchInput = document.getElementById('search-input');
                        searchInput.value = term; // Set the input to the clicked term
                        searchInput.focus(); // Focus the input field
                        searchInput.classList.add('expanded'); // Ensure it is expanded

                        // Redirect to the search page with the term
                        window.location.href = `/search?query=${encodeURIComponent(term)}`;
                    }
                });

                // Add click event to delete the history item
                deleteButton.addEventListener('click', function (event) {
                    event.stopPropagation(); // Prevent triggering the history item click event
                    deleteSearchHistory(term);
                });

                historyItem.appendChild(termText); // Append term text to history item
                historyItem.appendChild(deleteButton); // Append delete button to history item
                searchHistoryContainer.appendChild(historyItem); // Append history item to container
            }
        });
    } else {
        // If no history is found, show a message
        const noHistoryElement = document.createElement('div');
        noHistoryElement.classList.add('p-2', 'text-gray-500');
        noHistoryElement.textContent = 'No search history found.';
        searchHistoryContainer.appendChild(noHistoryElement);
    }

    // Append search history container to suggestionsDropdown
    suggestionsDropdown.appendChild(searchHistoryContainer);

    // Show dropdown for search history
    suggestionsDropdown.style.display = 'block';
}

// Delete search history item
function deleteSearchHistory(searchTerm) {
    let history = JSON.parse(localStorage.getItem(searchHistoryKey)) || [];
    // Remove the search term from the history array
    history = history.filter(item => item !== searchTerm);
    localStorage.setItem(searchHistoryKey, JSON.stringify(history));
    loadSearchHistory(); // Reload the history
}

// Function to clear all search history
document.getElementById('clear-history').addEventListener('click', function() {
    localStorage.removeItem(searchHistoryKey); // Remove the history from localStorage
    loadSearchHistory(); // Reload to reflect the cleared state
    alert('Search history cleared.');
});
