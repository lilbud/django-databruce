DataTable.type('num', 'className', 'dt-center');
DataTable.type('string', 'className', 'dt-left');
DataTable.type('date', 'className', 'dt-left');
DataTable.defaults.minDate = new Date('1965-01-01 00:00:00');
DataTable.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';
DataTable.defaults.column.orderSequence = ['asc', 'desc'];

function nextPage(table) {
  table.page('next').draw(false);
};

function prevPage(table) {
  table.page('previous').draw(false);
};

DataTable.feature.register('customOrder', function (settings, opts) {
  // 1. Validate that the user passed an external target dropdown selector
  let targetSelector = opts.selectId;
  if (!targetSelector) return null;

  let select = document.querySelector(targetSelector);
  if (select.length === 0) return null;

  // Create a native DataTable API instance for this specific table context
  let api = new DataTable.Api(settings);

  // Clear loading/placeholder items
  // select.empty();
  select.innerHTML = '';

  // 2. Loop through columns and read DataTables 2.0 standard native type() method
  api.columns().every(function (index) {
    let column = this;

    if (column.orderable()) {
      let headerText = column.header().textContent;
      let type = column.type(); // Modern native DT 2.0 type check
      const optionAsc = document.createElement('option');
      const optionDesc = document.createElement('option');

      optionAsc.value = `${index}-asc`;
      optionDesc.value = `${index}-desc`;

      // Standard text fallbacks
      let ascLabel = '(A-Z)';
      let descLabel = '(Z-A)';

      // Dynamically alter text strings depending on evaluated column contents
      if (type && type.includes('num')) {
        ascLabel = '(Least)';
        descLabel = '(Most)';
      } else if (type && type.includes('date')) {
        ascLabel = '(asc.)';
        descLabel = '(desc.)';
      }

      optionDesc.textContent = `${headerText} ${descLabel}`;
      optionAsc.textContent = `${headerText} ${ascLabel}`;

      select.appendChild(optionAsc);
      select.appendChild(optionDesc);
    }
  });

  // 3. Dropdown-to-Table Sync (Cleanly namespaced event)

  select.addEventListener('change', function (e) {
    let val = e.target.value;

    if (val) {
      let parts = val.split('-');
      let columnIndex = parseInt(parts[0], 10);
      let direction = parts[1];

      api.order([columnIndex, direction]).draw();
    }
  });

  // 4. Table-to-Dropdown Sync (Fires when header tags are clicked directly)
  api.on('order.dt.dtCustomOrder', function () {
    let currentOrder = api.order();
    if (currentOrder.length > 0) {
      let currentColumnIndex = currentOrder[0][0];
      let currentDirection = currentOrder[0][1];
      let targetValue = `${currentColumnIndex}-${currentDirection}`;

      // select.val(targetValue);
      select.value = targetValue;
    }
  });

  // Initialize immediate sync for default initial sorting state on boot
  api.trigger('order.dt');

  // DataTables 2.0 features return a DOM node if injecting objects into the layout.
  // Because our dropdown resides externally outside the table, we return null safely.
  return null;
});

// needed to fix pages with multiple tables behind tabs
Object.assign(DataTable.defaults, {
  searching: true,
  fixedHeader: {
    headerOffset: 52,
  },
  // scrollX: true,
  serverSide: true,
  processing: true,
  paging: true,
  // autoWidth: false,
  ordering: {
    indicators: false,
    handler: true,
  },
  pageLength: 50,
  search: {
    regex: true
  },
  responsive: {
    details: {
      type: ''
    }
  },
  layout: {
    topStart: {
      customOrder: {
        selectId: '#tableOrder'
      },
    },
  },
});





