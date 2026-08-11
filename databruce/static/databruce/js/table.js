function slugify(str) {
  if (!str) return '';

  return String(str)
    .toLowerCase() // Convert to lowercase
    .trim() // Trim leading/trailing whitespace
    .replace(/[^a-z0-9]+/g, '-') // Replace all spaces, underscores, and multiple hyphens with a single hyphen
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
}

function showTablePlaceholder($tbody, colCount, rowCount = 3) {
  const placeholderRows = Array(rowCount).fill(`
    <tr class="placeholder-row">
      <td colspan="${colCount}" class="p-0">
        <div class="placeholder-glow">
          <span class="placeholder col-12"></span>
        </div>
      </td>
    </tr>
  `).join('');

  $tbody.html(placeholderRows);
}

const getNestedValue = (obj, path) => {
  return path.split('.').reduce((acc, part) => acc?.[part], obj);
};

function rowGroup(data, groupVal) {
  return Object.groupBy(data ?? [], (item) => {
    return getNestedValue(item, groupVal) ?? "Unknown";
  });
}

async function createTable(url, columns, tableSelectorOrElem, options) {
  const $table = $(tableSelectorOrElem);
  const $tbody = $table.find('tbody').length ? $table.find('tbody') : $('<tbody>').appendTo($table);
  const colCount = $table.find('thead th').length || columns.length;

  // Show multiple placeholder rows
  // showTablePlaceholder($tbody, colCount, 3);

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    let data = await response.json();
    let table = $(tableSelectorOrElem);
    let tbody = table.find('tbody');

    if (!tbody.length) {
      table.append('<tbody></tbody>');
      tbody = table.find('tbody');
    }

    if (options && options.rowGroup) {
      data = rowGroup(data.results, options.rowGroup.groupVal);
    }

    // Create a DocumentFragment to minimize reflows
    const fragment = $(document.createDocumentFragment());

    if (options && options.rowGroup) {
      Object.entries(data).forEach(([key, value]) => {
        const columnsCount = tbody.closest('table').find('thead th').length || 2;
        let setHeader = $(`<tr class="set-header"><td class="py-0" colspan="${columnsCount}"><span>${key}</span></td></tr>`);

        if (key !== "Unknown") {
          fragment.append(setHeader);
        }

        value.forEach((rowVal) => {
          let row = $('<tr />');

          columns.forEach((col) => {
            const className = col.className ? `${col.className} ${col.data}` : col.data;
            const rawVal = rowVal[col.data];

            // Compute cell content
            let cellContent = col.render(rawVal, 'display', rowVal, null)

            let cell = $('<td />').html(cellContent).addClass(className);

            if (col.createdCell) {
              cell = col.createdCell(cell, cellContent, rowVal, null, 0) || cell;
            }

            if (options.createdRow) {
              row = options.createdRow(row, rowVal) || row;
            }

            row.append(cell);
          });

          fragment.append(row);
        });
      });

    }
    else {
      data.results.forEach((item) => {
        let row = $('<tr />');

        columns.forEach((col) => {
          const className = col.className ? `${col.className} ${col.data}` : col.data;
          const rawVal = item[col.data];

          // Compute cell content without mutating 'col'
          let cellContent = '';

          if (rawVal != null) {
            cellContent = col.render ? col.render(rawVal, 'display', item, null) : rawVal;
          }

          let cell = $('<td />').html(cellContent).addClass(className);

          row.append(cell);
        });
        fragment.append(row);
      });
    }

    // Append everything in a single DOM update
    tbody.empty().append(fragment);

  } catch (error) {
    console.error('Fetch operation failed:', error);
  }

  // Properly scope variables
  const tooltipTriggerList = Array.from(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map((el) => new bootstrap.Tooltip(el));
}