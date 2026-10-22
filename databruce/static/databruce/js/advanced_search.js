// this counter updates when a row is added or removed, used to set row/field specific IDs.
const totalForms = document.getElementById("id_form-TOTAL_FORMS");
const searchContainer = document.getElementById("setlist-search");

function formatSongOutput(result) {
  if (result.children) {
    const container = document.createElement('div');
    container.className = 'custom-select2-group';

    const span = document.createElement('span');
    span.className = 'group-title';
    span.textContent = result.text; // Safe from XSS injection

    container.appendChild(span);
    return container;
  }
  return result.text;
}

// endpoint-specific overrides
const URL_STRATEGIES = {
  songs: {
    minimumInputLength: 3,
    templateResult: formatSongOutput,
    processResults: (data) => {
      // Using native modern object grouping
      const grouped = Object.groupBy(data.results, (item) => item.original);

      const groupResults = Object.entries(grouped).map(([key, value]) => ({
        text: key === "true" ? "Originals" : "Covers",
        children: value
      }));

      return { results: groupResults };
    }
  },
  state: {
    minimumInputLength: 2
  }
};

function getOptions(ajax_url, element) {
  // Extract the specific route identifier (e.g., "songs" out of "songs" or dynamic paths)
  // Defaults to "default" if no specific configuration is found
  const key = Object.keys(URL_STRATEGIES).find(k => ajax_url?.includes(k)) || 'default';
  const strategy = URL_STRATEGIES[key] || {};

  // Safely extract dataset placeholders natively
  const placeholderText = element ? element.dataset.placeholder : '';

  // Standard baseline configuration
  return {
    theme: "bootstrap-5",
    selectionCssClass: "form-select-sm",
    dropdownCssClass: "form-select-sm",
    minimumInputLength: strategy.minimumInputLength || 3, // fallback to 3
    dropdownAutoWidth: true,
    dropdownPosition: 'below',
    placeholder: placeholderText, // fixed context reference
    allowClear: true,
    maximumSelectionLength: 3,
    width: '100%',

    // Merge template result if provided by strategy
    ...(strategy.templateResult && { templateResult: strategy.templateResult }),

    ajax: {
      delay: 250,
      url: ajax_url ? `/api/select2/${ajax_url}` : '',
      dataType: 'json',
      data: (params) => ({ name: params.term }),
      // Use strategy processing, or fall back to a clean default map
      processResults: strategy.processResults || ((data) => ({
        results: data.results.map(item => ({
          id: item.id,
          text: item.text
        }))
      }))
    }
  };
}

/**
 * Adjusts conjunctions between song rows.
 * Modified version of the one from Jerrybase, I couldn't figure this out
 * My changes are limited to condensing a few things using jQuery
 */
function adjust_conjunctions() {
  const rows = searchContainer.querySelectorAll('.conjunction-row');

  // remove conjunction row if it is first or last in search div
  if (rows.length > 0) rows[0].remove();
  if (rows.length > 1) rows[rows.length - 1].remove();

  // loop song rows
  searchContainer.querySelectorAll('.song-row').forEach(songRow => {
    const nextRow = songRow.nextElementSibling;

    if (nextRow && nextRow.classList.contains('conjunction-row') &&
      nextRow.nextElementSibling && nextRow.nextElementSibling.classList.contains('conjunction-row')) {
      nextRow.nextElementSibling.remove();
    } else if (nextRow && nextRow.classList.contains('song-row')) {
      songRow.insertAdjacentHTML('afterend', document.getElementById('conjunction').innerHTML);
    }
  });

  // Update conjunction text when select updated
  const conjunctionSelectVal = document.getElementById('conjunctionSelect').value;
  document.querySelectorAll('.conjunction').forEach(el => {
    el.innerHTML = conjunctionSelectVal;
  });
};

/**
 * Removes the selected row from the setlist search, decrement ID counter.
 * @param {object} button - rows remove button, used to find parent search row.
 */
function removeForm(button) {
  // Remove last song row using native closest
  button.closest('.song-row').remove();

  // Increment value of management form total count
  totalForms.value--;

  adjust_conjunctions();
}

/**
 * Show/hide the song2 field when position = followed_by
 * @param {object} row - parent row of the select element
 * @param {object} select - select element that triggered the change
 */
function positionChange(row, select) {
  const selectRow = select.closest('.song-row');
  const song2Input = selectRow.querySelector("[id*='song2']");
  const song2Parent = song2Input ? song2Input.parentElement : null;

  if (select.value === "followed_by") {
    if (song2Parent) song2Parent.style.display = '';
    $(song2Input).select2(getOptions('songs/', song2Input));
  } else {
    if (song2Parent) song2Parent.style.display = 'none';
  }
}

/**
 * Adds row to setlist search container, enables select2 on those fields as well
 */
function addForm() {
  // Row count for setting IDs
  const count = totalForms.value;
  const searchContainer = document.getElementById('setlist-search');

  // Grab hidden "template" row and add to search container
  searchContainer.insertAdjacentHTML('beforeend', document.getElementById('new_row').innerHTML);

  const songRows = searchContainer.querySelectorAll('.song-row');
  const row = songRows[songRows.length - 1];

  // Remove display none and show the new row
  row.id = `song-row-${count}`;
  row.classList.remove('d-none');

  // Adding incremented ids to fields
  const choiceEl = row.querySelector('.choice');
  if (choiceEl) {
    choiceEl.id = `id_form-${count}-choice`;
    choiceEl.name = `form-${count}-choice`;
  }

  const song1El = row.querySelector('.song1');
  if (song1El) {
    song1El.id = `id_form-${count}-song1`;
    song1El.name = `form-${count}-song1`;
    $(song1El).select2(getOptions('songs/', song1El));
  }

  const positionEl = row.querySelector('.position');

  if (positionEl) {
    positionEl.id = `id_form-${count}-position`;
    positionEl.name = `form-${count}-position`;
    positionEl.addEventListener('change', function () {
      positionChange(row, this);
    });
  }

  const song2El = row.querySelector('.song2');

  if (song2El) {
    song2El.id = `id_form-${count}-song2`;
    song2El.name = `form-${count}-song2`;
    if (song2El.parentElement) {
      song2El.parentElement.style.display = 'none';
    }
  }

  adjust_conjunctions();

  // Increment value of management form total count
  totalForms.value++;
}

document.addEventListener('DOMContentLoaded', () => {
  const rows = searchContainer ? searchContainer.querySelectorAll('.song-row') : [];
  const lastRow = rows[rows.length - 1];

  $('#start_date').mask('0000-00-00');
  $('#end_date').mask('0000-00-00');

  document.querySelectorAll('select[data-endpoint]').forEach((selectEl) => {
    const endpoint = selectEl.dataset.endpoint;
    $(selectEl).select2(getOptions(endpoint, selectEl));
  });

  // const venueSelect = document.getElementById('venue');

  // if (venueSelect) {
  //   var ts = new TomSelect('#venue', {
  //     valueField: 'id',
  //     labelField: 'text',
  //     searchField: 'text',
  //     // plugins: ['dropdown_header'],
  //     // fetch remote data
  //     shouldLoad: function (query) {
  //       return query.length >= 3;
  //     },
  //     load: function (query, callback) {
  //       var url = '/api/select2/venues/?name=' + encodeURIComponent(query);
  //       fetch(url)
  //         .then(response => response.json())
  //         .then(json => {
  //           console.log(json.results);
  //           callback(json.results);
  //         }).catch(() => {
  //           callback();
  //         });
  //     },
  //     render: {
  //       option: function (data, escape) {
  //         return `<div>
  //               <span class="name">${escape(data.text)}</span>
  //           </div>`;
  //       },
  //       item: function (data, escape) {
  //         return `<div>${escape(data.text)}</div>`;
  //       },
  //       no_results: function (data, escape) {
  //         // Replicates the exact message layout from your image
  //         return '<div class="ts-message">Please enter 3 or more characters</div>';
  //       },
  //       // Optional: Customizing the loading state if fetching remote data
  //       loading_more: function (data, escape) {
  //         return '<div class="ts-message">Loading more results...</div>';
  //       }
  //     }
  //   });

  //   ts.on('dropdown_open', function () {
  //     if (!ts.lastValue.length) {
  //       ts.refreshOptions(false);
  //     }
  //   });
  // }

  if (lastRow) {
    const song1 = lastRow.querySelector('.song1');
    const song2 = lastRow.querySelector('.song2');

    if (song2 && song2.parentElement) {
      song2.parentElement.style.display = 'none';
    }

    if (song1) {
      $(song1).select2(getOptions('songs/', song1));
    }

    // Modern Native Event Delegation for row positions
    lastRow.addEventListener('change', (event) => {
      const positionEl = event.target.closest('[class*=position]');
      if (positionEl) {
        positionChange(lastRow, positionEl);
      }
    });
  }

  document.getElementById('conjunctionSelect')?.addEventListener('change', adjust_conjunctions);
});