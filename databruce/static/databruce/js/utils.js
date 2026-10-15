
// Helper utility function for escaping HTML
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Helper utility function for rendering links
function renderLink(url, data, text) {
  return `<a href="${url}${data}">${text}</a>`
}

// Helper utility function for rendering event dates
function eventDateFormat(event) {
  if (!event) return '';

  const date = new Date(event.date || event);
  const dayText = date.toLocaleDateString('en-US', { weekday: 'long' });
  var dateItem;

  if (event.early_late) {
    dateItem = `<span class="text-primary">${event.date}</span><br><small>${event.early_late} • ${dayText}</small>`
  } else {
    dateItem = `<span class="text-primary">${event.date || event}</span><br><small>${dayText}</small>`
  }

  return event.event_id ? `<a href="/events/${event.event_id}">${dateItem}</a>` : event;
};

// Helper utility function for generating slugs
function slugify(str) {
  if (!str) return '';
  return String(str)
    .toLowerCase() // Convert to lowercase
    .trim() // Trim leading/trailing whitespace
    .replace(/[^a-z0-9]+/g, '-') // Replace all spaces, underscores, and multiple hyphens with a single hyphen
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
}

set_names = [
  "Show",
  "Set 1",
  "Set 2",
  "Encore",
  "Pre-Show",
  "Post-Show",
  "Public Rehearsal",
];

function reloadTooltips() {
  // Tooltip initialization was already Vanilla JS
  let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));

  tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}