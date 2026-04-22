/*!
 * Modified Bootstrap Theme Toggler
 */

(() => {
  'use strict'
  const getStoredTheme = () => localStorage.getItem('theme')
  const setStoredTheme = theme => localStorage.setItem('theme', theme)

  const getPreferredTheme = () => {
    const storedTheme = getStoredTheme()
    if (storedTheme) {
      return storedTheme
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  const setTheme = theme => {
    document.documentElement.setAttribute('data-bs-theme', theme)
  }

  const updateIcon = (theme) => {
    $('.theme-icon').hide();

    if (theme === 'dark') {
      $('.theme-icon.bi-moon-stars-fill').show();
      // $('#toggle-container').attr('data-bs-title', 'Toggle Theme (Light)');
    } else {
      $('.theme-icon.bi-sun-fill').show();
      // $('#toggle-container').attr('data-bs-title', 'Toggle Theme (Dark)');
    }
  }

  setTheme(getPreferredTheme())

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const storedTheme = getStoredTheme()
    console.log(storedTheme)
    if (storedTheme !== 'light' && storedTheme !== 'dark') {
      setTheme(getPreferredTheme())
    }
  })

  window.addEventListener('DOMContentLoaded', () => {
    var currentTheme = document.documentElement.getAttribute('data-bs-theme');

    updateIcon(currentTheme);

    $('.bd-theme-btn').on('click', function () {
      currentTheme = document.documentElement.getAttribute('data-bs-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

      setTheme(newTheme);
      setStoredTheme(newTheme);

      updateIcon(newTheme);
    })
  })
})()
