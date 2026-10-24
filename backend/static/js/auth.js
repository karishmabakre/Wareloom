
/* =====================================================
   WARELOOM - AUTHENTICATION JAVASCRIPT
   File: static/js/auth.js

   Responsibilities:
   1. Show/hide password
   2. Validate login form
   3. Validate signup form
   4. Display validation messages
   ===================================================== */

document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // -----------------------------------------------
    // 1. SHOW / HIDE PASSWORD
    // -----------------------------------------------

    document.querySelectorAll(".toggle-password").forEach(function (button) {
        button.addEventListener("click", function () {
            // The password input must be immediately before the button.
            const field = button.previousElementSibling;

            if (!field || !["password", "text"].includes(field.type)) {
                return;
            }

            const icon = button.querySelector("i");

            if (field.type === "password") {
                field.type = "text";

                if (icon) {
                    icon.className = "bi bi-eye-slash";
                }

                button.setAttribute("aria-label", "Hide password");
            } else {
                field.type = "password";

                if (icon) {
                    icon.className = "bi bi-eye";
                }

                button.setAttribute("aria-label", "Show password");
            }
        });
    });

    // -----------------------------------------------
    // 2. HELPER: DISPLAY ERROR MESSAGE
    // -----------------------------------------------

    function showError(messageElement, text) {
        if (!messageElement) {
            return;
        }

        messageElement.textContent = text;
        messageElement.style.color = "#d9534f";
        messageElement.setAttribute("role", "alert");
    }

    // -----------------------------------------------
    // 3. VALIDATE LOGIN AND SIGNUP FORMS ONLY
    // -----------------------------------------------

    const authForms = document.querySelectorAll(
        "#login-form, #signup-form"
    );

    authForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const message = form.querySelector(".form-message");

            if (message) {
                message.textContent = "";
                message.style.color = "";
            }

            const email = form.elements.namedItem("email");
            const password = form.elements.namedItem("password");

            // Validate email presence.
            if (!email || !email.value.trim()) {
                event.preventDefault();

                showError(message, "Please enter your email address.");

                if (email) email.focus();
                return;
            }

            // Validate password presence.
            if (!password || !password.value) {
                event.preventDefault();

                showError(message, "Please enter your password.");

                if (password) password.focus();
                return;
            }

            // Validate email format.
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (!emailPattern.test(email.value.trim())) {
                event.preventDefault();

                showError(message, "Please enter a valid email address.");
                email.focus();
                return;
            }

            // Login: validate only that a password was provided.
            if (form.id === "login-form") {
                return;
            }

            // ---------------------------------------
            // 4. SIGNUP-ONLY VALIDATION
            // ---------------------------------------

            const firstName = form.elements.namedItem("firstName");
            const lastName = form.elements.namedItem("lastName");

            if (!firstName || !firstName.value.trim()) {
                event.preventDefault();

                showError(message, "Please enter your first name.");

                if (firstName) firstName.focus();
                return;
            }

            if (!lastName || !lastName.value.trim()) {
                event.preventDefault();

                showError(message, "Please enter your last name.");

                if (lastName) lastName.focus();
                return;
            }

            const namePattern = /^[A-Za-z ]+$/;

            if (!namePattern.test(firstName.value.trim())) {
                event.preventDefault();

                showError(
                    message,
                    "First name should contain only letters and spaces."
                );

                firstName.focus();
                return;
            }

            if (!namePattern.test(lastName.value.trim())) {
                event.preventDefault();

                showError(
                    message,
                    "Last name should contain only letters and spaces."
                );

                lastName.focus();
                return;
            }

            // Signup password: at least 8 characters,
            // one uppercase, one lowercase, one digit,
            // and one special character.
            const strongPassword =
                /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/;

            if (!strongPassword.test(password.value)) {
                event.preventDefault();

                showError(
                    message,
                    "Password must contain at least 8 characters, " +
                    "including uppercase, lowercase, a number, " +
                    "and a special character."
                );

                password.focus();
                return;
            }
        });
    });
});
