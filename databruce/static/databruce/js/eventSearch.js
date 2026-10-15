let searchTimer;
let currentFocusIndex = -1; // Tracks the visually active search result
const resultsContainer = document.getElementById('results');
const searchInput = document.getElementById('eventSearch');
const clearBtn = document.getElementById('clearFloatingInput');
const myModal = document.getElementById('searchModal');
const bootstrapSearchModal = new bootstrap.Modal(myModal);

searchInput.value = '';

// Toggle visibility of the button based on input value
searchInput.addEventListener('input', () => {
  if (searchInput.value.trim() !== "") {
    clearBtn.classList.remove('d-none');
  } else {
    clearBtn.classList.add('d-none');
  }
});

// Action to clear the input and hide the button
clearBtn.addEventListener('click', () => {
  searchInput.value = '';
  clearBtn.classList.add('d-none');
  searchInput.focus();

  resultsContainer.style.display = 'none';
  resultsContainer.innerHTML = '';
});

// KEYDOWN LISTENER: Handles layout navigation and "Enter" execution
window.addEventListener('keydown', (event) => {
  // Check for Cmd (Mac) or Ctrl (Windows/Linux) + K
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault(); // Stop default browser search behaviors
    bootstrapSearchModal.show(); // Open the Bootstrap modal
  }
});

// Focus the search input when the modal is shown
myModal.addEventListener('shown.bs.modal', function () {
  searchInput.focus();
});

// INPUT LISTENER: Handles live search
searchInput.addEventListener('input', function (e) {
  const query = e.target.value;
  clearTimeout(searchTimer);

  if (searchInput.value.trim() !== "") {
    clearBtn.classList.remove('d-none');
  } else {
    clearBtn.classList.add('d-none');
  }

  // If the query is a date, format to YYYY-MM-DD
  if (/^\d/.test(query)) {
    const numbersOnly = query.replace(/\D/g, '');
    let formatted = '';

    if (numbersOnly.length > 0) formatted += numbersOnly.substring(0, 4);
    if (numbersOnly.length > 4) formatted += '-' + numbersOnly.substring(4, 6);
    if (numbersOnly.length >= 6) formatted += '-' + numbersOnly.substring(6, 8);
    e.target.value = formatted;
  }

  // Delay the search by 300ms
  searchTimer = setTimeout(function () {
    eventSearch(query);
  }, 300);
});

/**
 * Search for events based on query
 * @param {string} query
 */
function eventSearch(query) {
  // Clear the previous results and reset selection tracking
  const results = document.getElementById('results');
  currentFocusIndex = -1;

  if (results) {
    results.innerHTML = '';
    results.style.display = 'none';
  }

  // Only trigger search if input longer than 3 characters (length >= 4)
  if (query.length >= 4) {
    fetch(`/api/v1/events/?search=${query}`)
      .then(response => response.json())
      .then(data => {
        if (data.results && data.results.length > 0) {
          data.results.forEach(element => {
            resultsContainer.insertAdjacentHTML('beforeend',
              `<a href="/events/${element.event_id}" tabindex="-1" class="list-group-item search-item">
                ${element.date}<br>${element.venue.name} - ${element.artist.name || 'Unknown Artist'}
              </a>`
            );
          });
          resultsContainer.style.display = 'block';
        }
      })
      .catch(error => console.error('Error:', error));
  }
}


// KEYDOWN LISTENER: Handles layout navigation and "Enter" execution
searchInput.addEventListener('keydown', function (e) {
  // Grab all dynamically rendered list-group anchors
  const items = resultsContainer.querySelectorAll('.list-group-item');
  if (items.length === 0) return;

  if (e.key === 'ArrowDown') {
    e.preventDefault(); // Stop modal text wrapper or page scrolling
    currentFocusIndex++;
    if (currentFocusIndex >= items.length) currentFocusIndex = 0; // Wrap around to top
    setActiveItem(items);
  }
  else if (e.key === 'ArrowUp') {
    e.preventDefault(); // Stop modal text wrapper or page scrolling
    currentFocusIndex--;
    if (currentFocusIndex < 0) currentFocusIndex = items.length - 1; // Wrap around to bottom
    setActiveItem(items);
  }
  else if (e.key === 'Enter') {
    // If an item is highlighted, follow its link
    if (currentFocusIndex > -1 && items[currentFocusIndex]) {
      e.preventDefault(); // Prevent standard search form submission rules
      window.location.href = items[currentFocusIndex].href;
    }
  }
})

// HELPER: Manages the active visual classes and adjusts internal scroll context
function setActiveItem(items) {
  items.forEach(item => item.classList.remove('active'));

  if (currentFocusIndex > -1 && items[currentFocusIndex]) {
    const activeItem = items[currentFocusIndex];
    activeItem.classList.add('active');

    // Automatically scroll the inner modal container if active items overflow the view window
    activeItem.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest'
    });
  }
}