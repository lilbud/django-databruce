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
    const isDark = theme === 'dark';

    // Toggle 'd-none' based on whether the theme matches the icon
    document.querySelector('.theme-icon.bi-moon-stars-fill').classList.toggle('d-none', !isDark);
    document.querySelector('.theme-icon.bi-sun-fill').classList.toggle('d-none', isDark);
  }

  setTheme(getPreferredTheme())

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const storedTheme = getStoredTheme()

    if (storedTheme !== 'light' && storedTheme !== 'dark') {
      setTheme(getPreferredTheme())
    }
  })

  window.addEventListener('DOMContentLoaded', () => {
    var currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const themeBtn = document.querySelector('.bd-theme-btn');

    updateIcon(currentTheme);

    themeBtn.addEventListener('click', () => {
      currentTheme = document.documentElement.getAttribute('data-bs-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      setTheme(newTheme);
      setStoredTheme(newTheme);
      updateIcon(newTheme);
    })
  })
})()
