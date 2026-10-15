function tableSearch(table, searchID) {
  let searchTimeout;
  let lastSearchValue = ''; // Cache the last successfully sent search term

  const input = document.getElementById(searchID);
  if (!input) return;

  // Helper function to handle all search-related events
  const handleSearchEvent = function (e) {
    const value = this.value;

    // 1. If focus is lost (blur), instantly clear the typing timeout
    if (e.type === 'blur') {
      clearTimeout(searchTimeout);
    }

    // 2. Prevent server spam: Halt if the string hasn't changed
    if (value === lastSearchValue) {
      return;
    }

    // 3. Handle immediate execution conditions
    if (e.type === 'blur' || e.type === 'clear' || e.type === 'search') {
      clearTimeout(searchTimeout);
      lastSearchValue = value;
      // API signature: table.search( input, regex, smart, caseInsen )
      table.search(`${value}`, true, false, true).draw();
      return;
    }

    // 4. Fallback to debounced typing search
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      lastSearchValue = value;
      // API signature: table.search( input, regex, smart, caseInsen )
      table.search(`${value}`, true, false, true).draw();
    }, 400);
  };

  // Bind multiple event types since native addEventListener takes a single event name at a time
  const events = ['keyup', 'change', 'clear', 'blur', 'search'];
  events.forEach(eventType => {
    input.addEventListener(eventType, handleSearchEvent);
  });
}