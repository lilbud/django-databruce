DataTable.type('num', 'className', 'dt-center');
DataTable.type('string', 'className', 'dt-left');
DataTable.type('date', 'className', 'dt-left');
DataTable.defaults.minDate = new Date('1965-01-01 00:00:00');
DataTable.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';
// DataTable.defaults.column.columnControl = ['orderStatus', ['orderAsc', 'orderDesc', 'orderRemove', 'orderAddAsc', 'orderAddDesc']];
DataTable.defaults.column.orderSequence = ['asc', 'desc'];

set_names = [
  "Show",
  "Set 1",
  "Set 2",
  "Encore",
  "Pre-Show",
  "Post-Show",
];

DataTable.feature.register('customOrder', function (settings, opts) {
  // 1. Validate that the user passed an external target dropdown selector
  let targetSelector = opts.selectId;
  if (!targetSelector) return null;

  console.log(targetSelector);

  let select = $(targetSelector);
  if (select.length === 0) return null;

  // Create a native DataTable API instance for this specific table context
  let api = new DataTable.Api(settings);

  // Clear loading/placeholder items
  select.empty();

  // 2. Loop through columns and read DataTables 2.0 standard native type() method
  api.columns().every(function (index) {
    let column = this;

    if (column.orderable()) {
      let headerText = $(column.header()).text().trim();
      let type = column.type(); // Modern native DT 2.0 type check

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

      select.append(`<option value="${index}-asc">${headerText} ${ascLabel}</option>`);
      select.append(`<option value="${index}-desc">${headerText} ${descLabel}</option>`);
    }
  });

  // 3. Dropdown-to-Table Sync (Cleanly namespaced event)
  select.on('change.dtCustomOrder', function () {
    let val = $(this).val();
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

      select.val(targetValue);
    }
  });

  // Initialize immediate sync for default initial sorting state on boot
  api.trigger('order.dt');

  // DataTables 2.0 features return a DOM node if injecting objects into the layout.
  // Because our dropdown resides externally outside the table, we return null safely.
  return null;
});

DataTable.feature.register('customInputPaging', function (settings) {
  const api = new DataTable.Api(settings);

  // Create UI container elements
  const container = document.createElement('div');
  container.className = "d-flex flex-sm-row align-items-center justify-content-center column-gap-3 flex-wrap"
  container.id = "controls"

  const pagingContainer = document.createElement('div');
  pagingContainer.className = 'd-flex justify-content-center mb-2 mb-lg-0 align-items-center gap-2 order-2 col-12 col-lg-auto';
  pagingContainer.id = 'pagingControls';
  pagingContainer.innerHTML = `
        <button class="btn btn-sm btn-primary btn-prev" aria-label="Previous page"><i class="bi bi-chevron-left"></i></button>
        <input type="text" class="form-control form-control-sm text-center page-input m-0" min="1" value="1" style="width: 30px; height: calc(1.5em + 0.5rem + 2px);">
        <span class="total-pages align-middle">of 1</span>
        <button class="btn btn-sm btn-primary btn-next" aria-label="Next page"><i class="bi bi-chevron-right"></i></button>
    `;

  container.appendChild(pagingContainer);

  const tableInfo = document.createElement('div');
  tableInfo.className = 'dt-info order-3 table_info';
  tableInfo.id = 'table_info';
  tableInfo.setAttribute('aria-live', 'polite');
  tableInfo.setAttribute('role', 'status');
  container.appendChild(tableInfo);

  const input = container.querySelector('.page-input');
  const prevBtn = container.querySelector('.btn-prev');
  const nextBtn = container.querySelector('.btn-next');
  const totalSpan = container.querySelector('.total-pages');

  // Update UI whenever the table redraws / changes pages
  api.on('draw', () => {
    const pageInfo = api.page.info();
    input.value = pageInfo.page + 1;
    input.max = pageInfo.pages;
    totalSpan.textContent = `of ${pageInfo.pages || 1}`;

    // Handle button states
    prevBtn.disabled = pageInfo.page === 0;
    nextBtn.disabled = pageInfo.page >= pageInfo.pages - 1;
  });

  // Jump to page typed into input box
  input.addEventListener('change', () => {
    let val = parseInt(input.value, 10) - 1;
    const max = api.page.info().pages - 1;
    if (val < 0) val = 0;
    if (val > max) val = max;
    api.page(val).draw('page');
  });

  // Click navigation button events
  prevBtn.addEventListener('click', () => api.page('previous').draw('page'));
  nextBtn.addEventListener('click', () => api.page('next').draw('page'));

  return container;
});

$(window).on('resize', function () {
  DataTable.tables({
    visible: true,
    api: true
  })
    .columns.adjust()
    .responsive.recalc();
});

// needed to fix pages with multiple tables behind tabs
$('a[data-bs-toggle="tab"], button[data-bs-toggle="pill"], a[data-bs-toggle="pill"]').on('shown.bs.tab', function (e) {
  setTimeout(() => {
    let tables = DataTable.tables({
      visible: true,
      api: true
    });
    tables.columns.adjust();

    if (tables.responsive) {
      tables.responsive.recalc();
    }
  }, 50);
});


Object.assign(DataTable.defaults, {
  searching: true,
  fixedHeader: {
    headerOffset: 52,
  },
  info: true,
  scrollX: true,
  scrollCollapse: true,
  serverSide: true,
  processing: true,
  paging: true,
  autoWidth: true,
  ordering: {
    indicators: false,
    handler: true,
  },
  pageLength: 50,
  language: {
    info: "Showing _START_ to _END_ of _TOTAL_ entries",
    infoEmpty: "No records available",
    infoFiltered: "(filtered from _MAX_ total records)"
  },
  search: {
    regex: true
  },
  responsive: false,
  order: [],
  layout: {
    topStart: {
      customOrder: {
        selectId: '#tableOrder'
      },
    },
    bottomStart: null,
    topEnd: null,
    bottomEnd: null,
  },
});

function slugify(str) {
  if (!str) return '';
  return String(str)
    .toLowerCase() // Convert to lowercase
    .trim() // Trim leading/trailing whitespace
    .replace(/[^a-z0-9]+/g, '-') // Replace all spaces, underscores, and multiple hyphens with a single hyphen
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderLink(url, data, text) {
  return `<a href="${url}${data}">${text}</a>`
}

function eventDateFormat(event) {
  if (!event) return '';


  const date = new Date(event.date || event);
  const dayText = date.toLocaleDateString('en-US', { weekday: 'long' });
  var dateItem;

  if (event.early_late) {
    dateItem = `<span class="text-primary">${event.date}</span><br><small>${event.early_late} • ${dayText}</small>`
  } else {
    dateItem = `${event.date || event}<br><small>${dayText}</small>`
  }

  return event.event_id ? `<a href="/events/${event.event_id}">${dateItem}</a>` : event;
}