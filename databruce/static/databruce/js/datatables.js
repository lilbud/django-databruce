//DataTable.type('num', 'className', 'dt-center');
//DataTable.type('string', 'className', 'dt-left');
DataTable.defaults.minDate = new Date('1965-01-01 00:00:00');
DataTable.defaults.maxDate = new Date();
DataTable.Buttons.defaults.dom.button.className = 'btn';
DataTable.defaults.column.defaultContent = '';
DataTable.defaults.column.columnControl = ['orderStatus', ['orderAsc', 'orderDesc', 'orderRemove', 'orderAddAsc', 'orderAddDesc']];
DataTable.defaults.column.orderSequence = ['asc', 'desc'];

set_names = [
  "Show",
  "Set 1",
  "Set 2",
  "Encore",
  "Pre-Show",
  "Post-Show",
]

DataTable.feature.register('customInputPaging', function (settings) {
  const api = new DataTable.Api(settings);

  // Create UI container elements
  const container = document.createElement('div');
  container.className = 'd-inline-flex align-items-center justify-content-center gap-2 m-0';
  container.id = 'paging-container';
  container.innerHTML = `
        <button class="btn btn-sm border-0 btn-prev" aria-label="Previous page"><i class="bi bi-chevron-left"></i></button>
        <input type="text" class="form-control form-control-sm text-center page-input m-0" min="1" value="1" style="width: 30px; height: calc(1.5em + 0.5rem + 2px);">
        <span class="total-pages align-middle">of 1</span>
        <button class="btn btn-sm border-0 btn-next" aria-label="Next page"><i class="bi bi-chevron-right"></i></button>
    `;

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



$.extend(true, DataTable.defaults, {
  searching: true,
  fixedHeader: true,
  info: true,
  scrollX: true,
  scrollCollapse: true,
  serverSide: true,
  processing: true,
  paging: true,
  autoWidth: true,
  ordering: {
    indicators: false,
    handler: true
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
  // cardView: true,
  responsive: false,
  order: [],
  layout: {
    topStart: [],
    bottomStart: null,
    topEnd: null,
    bottomEnd: null,
    top: ['customInputPaging', 'info'],
    bottom: ['customInputPaging', 'info'],
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