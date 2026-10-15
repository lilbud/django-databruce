function showTablePlaceholder(tbody, colCount, rowCount = 3) {
  const placeholderRows = Array(rowCount).fill(`
    <tr class="placeholder-row">
      <td colspan="${colCount}" class="p-0">
        <div class="placeholder-glow">
          <span class="placeholder col-12"></span>
        </div>
      </td>
    </tr>
  `).join('');

  // tbody.html(placeholderRows);
  tbody.innerHTML = placeholderRows;
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
  let table = '';

  // check if table being passed is an element or a string
  try {
    table = document.querySelector(tableSelectorOrElem);
  } catch (error) {
    table = tableSelectorOrElem;
  }

  // const table = document.querySelector(tableSelectorOrElem);
  const tbody = table.querySelector('tbody') || table.appendChild(document.createElement('tbody'));
  const colCount = table.querySelector('thead th').length || columns.length;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    let data = await response.json();

    showTablePlaceholder(tbody, colCount, data.count);

    if (options && options.rowGroup) {
      data = rowGroup(data.results, options.rowGroup.groupVal);
    }

    tbody.innerHTML = '';

    if (options && options.rowGroup) {
      Object.entries(data).forEach(([key, value]) => {
        const setHeader = document.createElement('tr');
        setHeader.className = 'set-header';
        setHeader.innerHTML = `<td class="py-0" colspan="${colCount}"><span>${key}</span></td>`;

        if (key !== "Unknown") {
          tbody.append(setHeader);
        }

        value.forEach((rowVal) => {
          let row = document.createElement('tr');

          columns.forEach((col) => {
            const className = col.className ? `${col.className} ${col.data}` : col.data;
            const rawVal = rowVal[col.data];

            // Compute cell content
            let cellContent = col.render(rawVal, 'display', rowVal, null)

            let cell = document.createElement('td');
            cell.innerHTML = cellContent;
            cell.className = className;

            if (col.createdCell) {
              cell = col.createdCell(cell, cellContent, rowVal, null, 0) || cell;
            }

            if (options.createdRow) {
              row = options.createdRow(row, rowVal) || row;
            }

            row.append(cell);
          });

          tbody.append(row);
        });
      });
    }
    else {
      data.results.forEach((item) => {
        const row = document.createElement('tr');

        columns.forEach((col) => {
          const className = col.className ? `${col.className} ${col.data}` : col.data;
          const rawVal = item[col.data];
          const cell = document.createElement('td');
          cell.className = className;

          if (rawVal != null) {
            cell.innerHTML = col.render ? col.render(rawVal, 'display', item, null) : rawVal;
          }

          row.append(cell);
        });

        tbody.append(row);
      });
    }

    // tbody.innerHTML = '';
    // tbody.append(fragment);

  } catch (error) {
    console.error('Fetch operation failed:', error);
  }

  reloadTooltips();
}