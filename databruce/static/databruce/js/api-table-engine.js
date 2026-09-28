document.addEventListener("DOMContentLoaded", () => {
  // Automatically find and initialize every reusable table block on the current webpage
  document.querySelectorAll(".api-table-wrapper").forEach(initReusableTable);
});

function initReusableTable(wrapper) {
  const apiBaseUrl = wrapper.getAttribute("data-api-url");
  const tbody = wrapper.querySelector(".generic-table-body");
  const searchInput = wrapper.querySelector(".generic-table-search");
  const filterSelects = wrapper.querySelectorAll(".generic-table-filter");

  // UPDATED: Build a list of structural column configurations from the DOM headers
  const columnsConfig = Array.from(wrapper.querySelectorAll("thead th")).map(th => ({
    field: th.getAttribute("data-field"),
    type: th.getAttribute("data-type") || "text",
    className: th.getAttribute("class") || "text-start"
  }));

  // Helper function to resolve dot-notation paths safely
  function getNestedValue(obj, path) {
    if (!obj || !path) return '';
    return path.split('.').reduce((currentObject, key) => {
      return (currentObject && currentObject[key] !== undefined) ? currentObject[key] : undefined;
    }, obj) ?? '';
  }

  // NEW: Format data dynamically depending on column configuration type rules
  function formatValue(value, type) {
    if (type === "bool") {
      // Convert values strictly to true booleans
      const isTrue = value === true || value === "true" || value === 1 || value === "1";

      // Returns beautiful, scannable Bootstrap status badges instead of ugly raw text strings
      return isTrue
        ? `<span class="badge bg-success px-2 py-1">Yes</span>`
        : `<span class="badge bg-danger px-2 py-1">No</span>`;
    }

    // Default: Return raw textual strings directly
    return value;
  }

  async function fetchData() {
    // (fetchData remains exactly the same as prior steps...)
    tbody.innerHTML = `<tr><td colspan="${columnsConfig.length}" class="text-center text-muted">Loading data...</td></tr>`;
    const params = new URLSearchParams();
    if (searchInput && searchInput.value) params.append("search", searchInput.value);
    filterSelects.forEach(select => {
      if (select.value) params.append(select.getAttribute("data-filter-param"), select.value);
    });

    try {

      if (params.toString() === "") {
        var url = `${apiBaseUrl}`;
      } else {
        var url = `${apiBaseUrl}&${params.toString()}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      renderRows(data.results || data);
    } catch (error) {
      console.error("API Table Error:", error);
      tbody.innerHTML = `<tr><td colspan="${columnsConfig.length}" class="text-danger text-center">Error fetching records.</td></tr>`;
    }
  }

  // UPDATED: Applies formatValue() formatting rules on row insertion loops
  function renderRows(items) {
    tbody.innerHTML = "";

    if (!items || items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${columnsConfig.length}" class="text-center">No data records found.</td></tr>`;
      return;
    }

    items.forEach(item => {
      const row = document.createElement("tr");

      const rowCells = columnsConfig.map(col => {
        console.log(col)
        const rawValue = getNestedValue(item, col.field);
        const className = col.className || "";
        const formattedValue = formatValue(rawValue, col.type);
        return `<td class="${className}">${formattedValue}</td>`;
      }).join('');

      row.innerHTML = rowCells;
      tbody.appendChild(row);
    });
  }

  let debounceTimer;
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchData, 300);
    });
  }
  filterSelects.forEach(select => select.addEventListener("change", fetchData));
  fetchData();
}