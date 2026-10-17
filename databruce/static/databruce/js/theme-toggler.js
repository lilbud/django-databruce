/*!
 * Bootstrap Theme Toggler - Light / Dark / Auto Button Group
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
    if (theme === 'auto') {
      document.documentElement.setAttribute(
        'data-bs-theme',
        window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      )
    } else {
      document.documentElement.setAttribute('data-bs-theme', theme)
    }
  }

  // Apply preferred theme immediately on load
  setTheme(getPreferredTheme())

  const showActiveTheme = (theme) => {
    const btnAll = document.querySelectorAll('[data-bs-theme-value]')

    btnAll.forEach(element => {
      element.classList.remove('active', 'btn-neutral')
      element.setAttribute('aria-pressed', 'false')
    })

    const btnActive = document.querySelector(`[data-bs-theme-value="${theme}"]`)
    if (btnActive) {
      btnActive.classList.add('active', 'btn-neutral')
      btnActive.setAttribute('aria-pressed', 'true')
    }
  }

  // Listen for OS theme changes when in 'auto' mode
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const storedTheme = getStoredTheme()
    if (storedTheme === 'auto' || !storedTheme) {
      setTheme(getPreferredTheme())
    }
  })

  window.addEventListener('DOMContentLoaded', () => {
    // Default to 'auto' if no preference is stored
    const currentTheme = getStoredTheme() || 'auto'
    showActiveTheme(currentTheme)

    document.querySelectorAll('[data-bs-theme-value]').forEach(toggle => {
      toggle.addEventListener('click', () => {
        const theme = toggle.getAttribute('data-bs-theme-value')
        setStoredTheme(theme)
        setTheme(theme)
        showActiveTheme(theme)
      })
    })
  })
})()