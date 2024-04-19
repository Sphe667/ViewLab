// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // Example: Client-side form validation
    const registerForm = document.querySelector('#registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const usernameInput = document.querySelector('#username');
            const emailInput = document.querySelector('#email');
            const passwordInput = document.querySelector('#password');
            const confirmPasswordInput = document.querySelector('#confirmPassword');

            if (!usernameInput.value.trim() || !emailInput.value.trim() || !passwordInput.value || !confirmPasswordInput.value) {
                event.preventDefault();
                alert('All fields are required!');
            } else if (passwordInput.value !== confirmPasswordInput.value) {
                event.preventDefault();
                alert('Passwords do not match!');
            }
        });
    }

    // Example: AJAX request to fetch available labs
    const dashboard = document.querySelector('#dashboard');
    if (dashboard) {
        fetch('/api/labs')
            .then(response => response.json())
            .then(data => {
                const labsList = document.querySelector('#labsList');
                data.labs.forEach(lab => {
                    const listItem = document.createElement('li');
                    listItem.textContent = lab.name;
                    labsList.appendChild(listItem);
                });
            })
            .catch(error => console.error('Error fetching labs:', error));
    }
});
