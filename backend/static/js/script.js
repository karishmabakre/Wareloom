
/* =====================================================
   WARELOOM - NAVIGATION JAVASCRIPT
   File: static/js/script.js

   Responsibilities:
   1. Desktop dropdown menus
   2. Mobile navigation toggle
   3. Close menus when clicking outside
   4. Escape key support
   5. Responsive navigation
   ===================================================== */

document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    const header = document.querySelector(".site-header");
    const navMenu = document.querySelector("#mainMenu");
    const mobileToggle = document.querySelector(".mobile-toggle");

    const dropdownItems = Array.from(
        document.querySelectorAll(".dropdown-item-custom")
    );

    const desktopQuery = window.matchMedia("(min-width: 901px)");

    // Navigation may not exist on every page.
    // Do not stop other JavaScript files from running.
    if (!header || !navMenu || !mobileToggle) {
        return;
    }

    function isDesktop() {
        return desktopQuery.matches;
    }

    // Close all dropdowns except an optional selected item.
    function closeDropdowns(exceptItem = null) {
        dropdownItems.forEach(function (item) {
            if (item === exceptItem) return;

            item.classList.remove("is-open");

            const trigger = item.querySelector(".nav-link-custom");

            if (trigger) {
                trigger.setAttribute("aria-expanded", "false");
            }
        });
    }

    // Open or close a specific dropdown.
    function setDropdown(item, shouldOpen) {
        const trigger = item.querySelector(".nav-link-custom");

        if (!trigger) return;

        if (shouldOpen) {
            closeDropdowns(item);
            item.classList.add("is-open");
            trigger.setAttribute("aria-expanded", "true");
        } else {
            item.classList.remove("is-open");
            trigger.setAttribute("aria-expanded", "false");
        }
    }

    // Open the mobile menu.
    function openMobileMenu() {
        navMenu.classList.add("is-mobile-open");

        mobileToggle.setAttribute("aria-expanded", "true");
        mobileToggle.setAttribute("aria-label", "Close navigation menu");

        document.body.classList.add("menu-open");
    }

    // Close the mobile menu.
    function closeMobileMenu() {
        navMenu.classList.remove("is-mobile-open");

        mobileToggle.setAttribute("aria-expanded", "false");
        mobileToggle.setAttribute("aria-label", "Open navigation menu");

        document.body.classList.remove("menu-open");

        closeDropdowns();
    }

    // Mobile navigation button.
    mobileToggle.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        if (navMenu.classList.contains("is-mobile-open")) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    });

    // Configure each navigation dropdown.
    dropdownItems.forEach(function (item) {
        const trigger = item.querySelector(".nav-link-custom");

        if (!trigger) return;

        trigger.setAttribute("aria-haspopup", "true");
        trigger.setAttribute("aria-expanded", "false");

        // Desktop hover behavior.
        item.addEventListener("mouseenter", function () {
            if (isDesktop()) {
                setDropdown(item, true);
            }
        });

        item.addEventListener("mouseleave", function () {
            if (isDesktop()) {
                setDropdown(item, false);
            }
        });

        // Click behavior for desktop and mobile.
        trigger.addEventListener("click", function (event) {
            if (!item.querySelector(".dropdown-panel")) {
                return;
            }

            event.preventDefault();

            const currentlyOpen = item.classList.contains("is-open");

            setDropdown(item, !currentlyOpen);
        });

        // Keyboard support.
        trigger.addEventListener("keydown", function (event) {
            if (event.key === "ArrowDown") {
                event.preventDefault();

                setDropdown(item, true);

                const firstLink = item.querySelector(
                    ".dropdown-column a"
                );

                if (firstLink) {
                    firstLink.focus();
                }
            }
        });
    });

    // Close menus after selecting a dropdown destination.
    document.querySelectorAll(".dropdown-panel a").forEach(function (link) {
        link.addEventListener("click", function () {
            closeDropdowns();

            if (!isDesktop()) {
                closeMobileMenu();
            }
        });
    });

    // Close menus when clicking outside the header.
    document.addEventListener("click", function (event) {
        if (!header.contains(event.target)) {
            closeDropdowns();

            if (!isDesktop()) {
                closeMobileMenu();
            }
        }
    });

    // Escape key closes open navigation.
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeDropdowns();

            if (!isDesktop()) {
                closeMobileMenu();
            }
        }
    });

    // Reset mobile navigation when changing screen sizes.
    function handleBreakpointChange() {
        closeDropdowns();

        navMenu.classList.remove("is-mobile-open");

        mobileToggle.setAttribute("aria-expanded", "false");
        mobileToggle.setAttribute("aria-label", "Open navigation menu");

        document.body.classList.remove("menu-open");
    }

    if (desktopQuery.addEventListener) {
        desktopQuery.addEventListener("change", handleBreakpointChange);
    } else {
        desktopQuery.addListener(handleBreakpointChange);
    }

    console.log("Wareloom navigation initialized.");
});
