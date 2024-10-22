const searchHistoryKey = 'searchHistory'; // LocalStorage key for storing search history

// Save search to history with associated URL
function saveSearchHistory(searchTerm, searchUrl) {
    let history = JSON.parse(localStorage.getItem(searchHistoryKey)) || [];
    
    // Check if the search term already exists
    const existingItem = history.find(item => item.term.toLowerCase() === searchTerm.toLowerCase());
    
    // If it doesn't exist, add it to history
    if (!existingItem) {
        history.push({ term: searchTerm, url: searchUrl });
    }
    
    // Save the updated history back to localStorage
    localStorage.setItem(searchHistoryKey, JSON.stringify(history));
    loadSearchHistory();
}

// Load search history
function loadSearchHistory() {
    const suggestionsDropdown = document.getElementById('suggestions-dropdown');
    suggestionsDropdown.innerHTML = ''; // Clear previous content

    let history = JSON.parse(localStorage.getItem(searchHistoryKey)) || [];
    
    // Create container for history
    const searchHistoryContainer = document.createElement('div');
    searchHistoryContainer.classList.add('search-history-container', 'border-t', 'pt-2');

    // Check if history is empty
    if (history.length > 0) {
        history.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.classList.add('history-item', 'p-2', 'flex', 'justify-between', 'hover:bg-gray-200', 'cursor-pointer');
            historyItem.innerHTML = `
                <span>${item.term}</span>
                <a class="bi bi-x delete-history-item px-2 p-1 hover:bg-gray-300 rounded-md"></a>
            `;

            // Add click event to redirect to the stored URL
            historyItem.addEventListener('click', function () {
                window.location.href = item.url; // Redirect to the URL stored with the search term
            });

            // Add click event to delete the history item
            historyItem.querySelector('.delete-history-item').addEventListener('click', function (event) {
                event.stopPropagation(); // Prevent triggering the history item click event
                deleteSearchHistory(item.term);
            });

            searchHistoryContainer.appendChild(historyItem);
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
    history = history.filter(item => item.term.toLowerCase() !== searchTerm.toLowerCase());
    localStorage.setItem(searchHistoryKey, JSON.stringify(history));
    loadSearchHistory(); // Reload the history
}

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

// Update the suggestions based on input
document.getElementById('search-input').addEventListener('input', function () {
    const inputText = this.value.toLowerCase();
    const suggestionsDropdown = document.getElementById('suggestions-dropdown');

    // Reference to the searchSuggestionsElement (from dataset attributes)
    const searchSuggestionsElement = document.getElementById('search-suggestions'); // Assuming this is the correct element

    // List of suggestions with corresponding URLs
    const suggestions = [
        { name: 'Dashboard', url: searchSuggestionsElement.dataset.dashboardUrl },
        { name: 'Homeowners', url: searchSuggestionsElement.dataset.homeownersUrl },
        { name: 'Residents', url: searchSuggestionsElement.dataset.residentsUrl },
        { name: 'Pending Accounts', url: searchSuggestionsElement.dataset.pendingAccountsUrl },
        { name: 'Properties', url: searchSuggestionsElement.dataset.propertiesUrl },
        { name: 'Maintenance', url: searchSuggestionsElement.dataset.maintenanceUrl },
        { name: 'Maintenance Personnel', url: searchSuggestionsElement.dataset.maintenancePersonnelUrl },
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

        if (filteredSuggestions.length > 0) {
            filteredSuggestions.forEach(suggestion => {
                const regex = new RegExp(`(${inputText})`, 'gi');
                const suggestionElement = document.createElement('div');
                suggestionElement.innerHTML = suggestion.name.replace(regex, '<span class="highlight">$1</span>');
                suggestionElement.classList.add('p-2', 'cursor-pointer', 'hover:bg-gray-200');

                // Add event listener for redirecting on click and saving the search history
                suggestionElement.addEventListener('mousedown', function () {
                    window.location.href = suggestion.url; // Redirect to the selected suggestion's URL
                    saveSearchHistory(suggestion.name, suggestion.url); // Save term and URL to history
                });

                suggestionsDropdown.appendChild(suggestionElement);
            });
        } else {
            const noResultsElement = document.createElement('div');
            noResultsElement.classList.add('p-2', 'text-gray-500', 'flex', 'items-center');
            noResultsElement.innerHTML = `
                <span class="material-icons mr-2">warning</span>
                No results found
            `;
            suggestionsDropdown.appendChild(noResultsElement);
        }

        suggestionsDropdown.style.display = 'block';
    } else {
        loadSearchHistory(); // Show search history when input is empty
    }
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

// Prevent the search input from collapsing when clicking inside the suggestions dropdown
document.getElementById('suggestions-dropdown').addEventListener('mousedown', function(event) {
    event.preventDefault(); // Prevent blur and collapse when clicking on suggestions
});
