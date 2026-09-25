event_table_columns = [
  {
    'data': 'user_present',
    'name': 'user_present',
    'width': '1rem',
    'className': 'text-center text-xs user-present',
    'orderable': false,
    'searchable': false,
    'columnControl': [],
    'render': function (data, type, row, meta) {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
      return renderAttendanceForm(row, csrfToken);
    },
  },
  {
    'data': 'date',
    'name': 'event_id',
    'type': 'date',
    'width': '6rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      return eventDateFormat(row);
    },
  },
  {
    'data': 'has_setlist',
    'name': 'has_setlist',
    'width': '1rem',
    'className': 'text-center text-xs setlist',
    'orderable': false,
    'searchable': false,
    'columnControl': [],
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
      return data ? `<a href="/bands/${data.uuid}">${data.name}</a>` : '';
    },
  },
  {
    'data': 'venue',
    'name': 'venue__name, venue__detail, venue__city__name, venue__city__state__abbrev, venue__city__state__name, venue__city__country__name',
    'className': 'text-nowrap',
    'width': '12rem',
    'render': function (data, type, row, meta) {
      if (data) {
        return row.city ? `<a href="/venues/${data.uuid}">${data.name}</a><br><small>${row.city}</small>` : `<a href="/venues/${data.uuid}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'tour',
    'name': 'tour__name',
    'width': '10rem',
    'className': 'text-wrap',
    'render': function (data, type, row, meta) {
      if (data) {
        return row.leg ? `<a href="/tours/${data.slug}">${data.name}</a><br><small>${row.leg}</small>` : `<a href="/tours/${data.slug}">${data.name}</a>`
      }
    },
  },
  {
    'data': 'title',
    'name': 'title',
    'width': '15rem',
    'render': function (data, type, row, meta) {
      return row.event_status ? `<span class="text-danger fw-semibold">[${row.type[0]}] ${data || ''}</span>` : data
    },
  },
  {
    'data': 'public',
    'name': 'public',
    'visible': false,
    'orderable': false,
    'render': function (data, type, row, meta) {
      if (data != null) {
        return data;
      }
    },
  },
]

function eventTable(url) {
  var table = new DataTable('#eventTable', {
    ajax: {
      'url': url,
    },
    layout: {
      topStart: {
        customOrder: {
          selectId: '#eventTableOrder'
        }
      }
    },
    responsive: {
      details: false,
    },
    autoWidth: false,
    pageLength: 100,
    columns: event_table_columns,
    order: [[1, 'asc']],
    initComplete: function (settings, json) {
      var api = this.api();
      var info = api.page.info();
      $('#event-count-badge').text(info.recordsTotal);

      const input = $('.event-controls .page-input');
      const prevBtn = $('.event-controls .btn-prev');
      const nextBtn = $('.event-controls .btn-next');
      const totalSpan = $('.event-controls .total-pages');

      // Initial button states
      input.val(info.page + 1);
      prevBtn.attr('disabled', info.page === 0);
      nextBtn.attr('disabled', info.page >= info.pages - 1);

      $('#eventTableInfo').text(`Showing ${info.start + 1} to ${info.end} of ${info.recordsTotal} entries`);

      api.on('draw', () => {
        const pageInfo = api.page.info();

        input.val(pageInfo.page + 1);
        input.attr('max', pageInfo.pages);

        totalSpan.text(`of ${pageInfo.pages || 1}`);

        // Handle button states
        prevBtn.attr('disabled', pageInfo.page === 0);
        nextBtn.attr('disabled', pageInfo.page >= pageInfo.pages - 1);

        // FIX: Swapped out 'info' for 'pageInfo' so it updates dynamically
        $('#eventTableInfo').text(`Showing ${pageInfo.start + 1} to ${pageInfo.end} of ${pageInfo.recordsTotal} entries`);
      });

      totalSpan.text(`of ${info.pages || 1}`);

      nextBtn.on('click', function () {
        table.page('next').draw(false);
      });

      prevBtn.on('click', function () {
        table.page('previous').draw(false);
      });

      input.on('change', function () {
        let val = parseInt(this.value, 10) - 1;
        const max = api.page.info().pages - 1;
        if (val < 0) val = 0;
        if (val > max) val = max;

        input.attr('value', val);

        api.page(val).draw('page');
      });

      let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));

      tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
      });
    }
  });

  table.on('xhr.dt', function (e, settings, json) {
    if (!json || !json.data) return;

    // Re-render your card layout using the current page's results
    renderCards(json.data);
  });

  tableSearch(table, 'search');

  $('.publicity-filter').on('change', function () {
    var selectedValue = this.value;
    table.order([[1, 'asc']]).column(7).search(selectedValue ? selectedValue : '', true, false).draw();
  });
}

$(document).on('submit', '.userForm', async function (e) {
  e.preventDefault();
  const formData = new FormData(this);
  const addBtn = $(this).find('#add');

  let action = addBtn.attr('data-action');
  let event = addBtn.attr('data-event');
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

    addBtn
      .toggleClass('bi-star-fill', isAdded)
      .toggleClass('bi-star', !isAdded)
      .attr('data-attended', isAdded ? 'true' : 'false')
      .attr('data-action', isAdded ? 'remove' : 'add');

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