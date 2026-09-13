let searchTimer;
let currentFocusIndex = -1; // Tracks the visually active search result
const resultsContainer = document.getElementById('results');

const searchInput = document.getElementById('eventSearch');
const clearBtn = document.getElementById('clearFloatingInput');

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
  $('#results').empty();
});

const myModal = document.getElementById('searchModal');
const bootstrapSearchModal = new bootstrap.Modal(myModal);

window.addEventListener('keydown', (event) => {
  // Check for Cmd (Mac) or Ctrl (Windows/Linux) + K
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault(); // Stop default browser search behaviors
    bootstrapSearchModal.show(); // Open the Bootstrap modal
  }
});

myModal.addEventListener('shown.bs.modal', function () {
  searchInput.focus();
});

$("form").on("keydown", "input:not(textarea)", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
});

$('#eventSearch').on('input', function () {
  const query = $(this).val();
  clearTimeout(searchTimer);

  // If the query is a date, format to YYYY-MM-DD
  if (/^\d/.test(query)) {
    let numbersOnly = query.replace(/\D/g, '');
    let formatted = '';

    if (numbersOnly.length > 0) formatted += numbersOnly.substring(0, 4);
    if (numbersOnly.length > 4) formatted += '-' + numbersOnly.substring(4, 6);
    if (numbersOnly.length >= 6) formatted += '-' + numbersOnly.substring(6, 8);
    $(this).val(formatted);
  }

  // Delay the search by 300ms
  searchTimer = setTimeout(function () {
    eventSearch(query);
  }, 300);
});

function eventSearch(query) {
  // Clear the previous results and reset selection tracking
  $('#results').empty().hide();
  currentFocusIndex = -1;

  // Only trigger search if input longer than 3 characters (length >= 4)
  if (query.length >= 4) {
    fetch(`/api/v1/events/?search=${query}`)
      .then(response => response.json())
      .then(data => {
        if (data.results && data.results.length > 0) {
          data.results.forEach(element => {
            $(resultsContainer).append(
              `<a href="/events/${element.event_id}" tabindex="-1" class="list-group-item search-item">
                ${element.date}<br>${element.venue.name} - ${element.artist.name}
              </a>`
            );
          });
          $(resultsContainer).show();
        }
      })
      .catch(error => console.error('Error:', error));
  }
}

// KEYDOWN LISTENER: Handles layout navigation and "Enter" execution
$('#eventSearch').on('keydown', function (e) {
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
});

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