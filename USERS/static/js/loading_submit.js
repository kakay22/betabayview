document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('form');
    var loader = document.getElementById('pre-loader');

    form.addEventListener('submit', function(event) {
        loader.style.display = 'flex';  // Show the loader
    });
});
