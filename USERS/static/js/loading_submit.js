document.addEventListener('DOMContentLoaded', function() {
    // Select all <form> tags in the document
    const forms = document.querySelectorAll('form');
    
    // Select the loading spinner
    const loader = document.getElementById('loadingSpinner');

    // Log the forms to the console
    forms.forEach((form) => {
        // Event listener for form submission
        form.addEventListener('submit', function(event) {
            // Show the loader
            loader.classList.remove('hidden');
        });
    });
});
