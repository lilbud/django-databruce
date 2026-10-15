event_table_defs = [
  { targets: [0, 2, 7], width: '1rem', orderable: false, columnControl: [] },
  { targets: [0, 2], orderable: false, searchable: false },
  { targets: [7], visible: false },
]

event_table_columns = [
  {
    'data': 'user_present',
    'name': 'user_present',
    'className': 'text-center text-xs',
    'render': function (data, type, row, meta) {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
      return renderAttendanceForm(row, csrfToken);
    },
  },
  {
    'data': 'date',
    'name': 'event_id, date, early_late',
    'type': 'date',
    'width': '6rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      return eventDateFormat(row);
    },
  },
  {
    'data': 'setlist',
    'name': 'setlist',
    'className': 'text-center text-xs',
    'render': function (data, type, row, meta) {
      return data ? `<i class="bi bi-check-lg"></i>` : ''
    },
  },
  {
    'data': 'artist',
    'name': 'artist__name',
    'className': 'text-wrap',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      return data ? `<a href="/bands/${data.slug}">${data.name}</a>` : '';
    },
  },
  {
    'data': 'venue',
    'name': 'venue__name, venue__detail, venue__city__name, venue__city__state__abbrev, venue__city__state__name, venue__city__country__name',
    'className': 'text-nowrap',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      return data ? `<a href="/venues/${data.slug}">${data.name}<br><small>${row.city}</small></a>` : ``
    },
  },
  {
    'data': 'tour',
    'name': 'tour__name',
    'width': '12rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      return data ? `<a href="/tours/${data.slug}">${data.name}</a>${row.leg ? `<br><small>${row.leg}</small>` : ''}` : '';
    },
  },
  {
    'data': 'title',
    'name': 'title',
    'width': '15rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      return row.event_status ? `<span class="text-danger fw-semibold">[${row.type[0]}] ${data || ''}</span>` : data
    },
  },
  {
    'data': 'public',
    'name': 'public',
    'render': function (data, type, row, meta) {
      return data;
    },
  },
]

function eventTable(url) {
  var table = new DataTable('#eventTable', {
    ajax: {
      'url': url,
    },
    on: {
      // Plain JS callback mapping arguments directly
      xhr: function (e, settings, json, xhr) {
        if (!json || !json.data) return;
        renderCards(json.data);
        reloadTooltips();
      }
    },
    layout: {
      topStart: {
        customOrder: {
          selectId: '#eventTableOrder'
        }
      }
    },
    scrollX: true,
    autoWidth: false,
    pageLength: 100,
    columnDefs: event_table_defs,
    columns: event_table_columns,
    order: [[1, 'asc']],
    initComplete: function (settings, json) {
      var api = this.api();
      var info = api.page.info();

      const eventCountBadge = document.getElementById('event-count-badge');

      if (eventCountBadge) {
        eventCountBadge.textContent = info.recordsTotal;
      }

      const input = document.querySelectorAll('.event-controls .page-input');
      const prevBtn = document.querySelectorAll('.event-controls .btn-prev');
      const nextBtn = document.querySelectorAll('.event-controls .btn-next');
      const totalSpan = document.querySelectorAll('.event-controls .total-pages');
      const tableInfo = document.querySelector('.event_table_info');

      // Initial button states
      input.forEach(el => {
        el.value = info.page + 1;

        el.addEventListener('change', function () {
          let val = parseInt(this.value, 10) - 1;
          const max = api.page.info().pages - 1;

          if (val < 0) val = 0;
          if (val > max) val = max;

          this.value = val;
          api.page(val).draw('page');
        })
      });

      prevBtn.forEach(el => {
        el.disabled = info.page === 0;

        el.addEventListener('click', function () {
          prevPage(table);
        });
      });

      nextBtn.forEach(el => {
        el.disabled = info.page >= info.pages - 1;

        el.addEventListener('click', function () {
          nextPage(table);
        });
      });

      tableInfo.textContent = `Showing ${info.start + 1} to ${info.end} of ${info.recordsTotal} entries`;

      api.on('draw', () => {
        const pageInfo = api.page.info();

        input.forEach(el => {
          el.value = pageInfo.page + 1;
          el.setAttribute('max', pageInfo.pages);
        });

        totalSpan.forEach(el => {
          el.textContent = `of ${pageInfo.pages || 1}`;
        });

        prevBtn.forEach(el => {
          el.disabled = pageInfo.page === 0;
        });

        nextBtn.forEach(el => {
          el.disabled = pageInfo.page >= pageInfo.pages - 1;
        });

        tableInfo.textContent = `Showing ${pageInfo.start + 1} to ${pageInfo.end} of ${pageInfo.recordsTotal} entries`;
      });

      // totalSpan.textContent = `of ${info.pages || 1}`;
      totalSpan.forEach(el => {
        el.textContent = `of ${info.pages || 1}`;
      })

      reloadTooltips();
    }
  });

  tableSearch(table, 'search');

  const publicityFilter = document.getElementById('PublicityFilter');

  publicityFilter.addEventListener('change', function () {
    var selectedValue = this.value;
    table.order([[1, 'asc']]).column(7).search(selectedValue ? selectedValue : '', true, false).draw();
  });
}

document.addEventListener('submit', async function (e) {
  // Find the closest matching form if it's part of the event delegation
  const form = e.target.closest('.userForm');
  if (!form) return;

  e.preventDefault();

  const formData = new FormData(form);
  const addBtn = form.querySelector('#add');

  let action = addBtn.getAttribute('data-action');
  let event = addBtn.getAttribute('data-event');

  const url = `/events/${event}/${action}/`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    const isAdded = data['action'] === 'added';

    addBtn.classList.toggle('bi-star-fill', isAdded);
    addBtn.classList.toggle('bi-star', !isAdded);
    addBtn.setAttribute('data-attended', isAdded ? 'true' : 'false');
    addBtn.setAttribute('data-action', isAdded ? 'remove' : 'add');

  } catch (error) {
    console.error('Error during POST request:', error);
  }
});

function renderAttendanceForm(event, csrfToken) {
  if (!event.public) return "";

  const isAttending = event.user_present;
  const iconClass = isAttending ? "bi-star-fill" : "bi-star";
  const action = isAttending ? "remove" : "add";
  const attended = isAttending ? "true" : "false";
  const blockedTypes = ["Rescheduled", "Cancelled", "Relocated", "No Gig"];

  if (blockedTypes.includes(event.type?.[0]?.name)) {
    return "";
  }

  return `
    <span data-bs-toggle="tooltip" data-bs-title="${isAttending ? "Remove from profile" : "Add to profile"}">

    <form method="post" id="userForm" class="userForm d-flex justify-content-center align-items-center">
      <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
      <button
        type="submit"
        class="btn btn-link p-0 border-0 bi ${iconClass} star-btn"
        data-event="${event.id}"
        data-action="${action}"
        data-attended="${attended}"

        id="add"
      ></button>
    </form>
    </span>
  `;
}