

function initializeShareCardGenerator(config) {
  document.getElementById(config.buttonId).addEventListener('click', function () {
    const button = this;
    const originalText = button.innerHTML;
    const width = 540;

    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm py-auto" role="status"></span> Generating Image...';

    fetch(window.location.href, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(response => response.text())
      .then(htmlContent => {
        const sandbox = document.createElement('div');
        sandbox.style.position = 'fixed';
        sandbox.style.top = '-9999px';
        sandbox.style.left = '-9999px';
        sandbox.style.width = `${width}px`;

        sandbox.innerHTML = htmlContent;
        document.body.appendChild(sandbox);

        const $sandboxTable = $(sandbox).find('#setlistTable');

        if (config.activeTheme === 'dark') {
          sandbox.setAttribute('data-bs-theme', 'dark');
        } else {
          sandbox.setAttribute('data-bs-theme', 'light');
        }

        var url = config.ajaxUrl;

        let setlistOptions = {
          createdRow: function (row, data) {
            row.addClass(slugify(data.set_name));

            var allowedSets = ['Show', 'Set 1', "Set 2", 'Encore', 'Pre-Show', 'Post-Show', 'Rehearsal', 'Soundcheck']

            if (allowedSets.includes(data.set_name)) {
              var album = data.song.category_slug;
              row.attr('data-album', album);
            }

            return row
          },
          rowGroup: {
            groupVal: 'set_name'
          }
        }

        let setlistColumns = [
          {
            'data': 'song_num',
            'className': 'text-center',
            'width': '',
            'render': function (data, type, row, meta) {
              if (data) {
                return data
              }

              return ''
            },
            'createdCell': function (td, cellData, rowData, row, col) {
              $(td).addClass('songnum');

              if (rowData.position) {
                var position = slugify(rowData.position);
                $(td).addClass(`${position} position`).attr('data-bs-toggle', 'tooltip').attr('data-bs-title', rowData.position).attr('data-bs-html', true)
              }

              return td;
            },
          },
          {
            'data': 'song',
            'className': 'text-wrap',
            'width': '',
            'render': function (data, type, row, meta) {
              const songLink = `<a class="text-reset" href="/songs/${data.slug}">${data.name}</a>`;
              const segue = row.segue ? ' <span class="segue"></span>' : '';

              const activeBadges = SONG_BADGES
                .filter(b => row[b.key])
                .map(b => createBadge(b.class, b.label, b.title))

              const tourBadge = getTourPositionBadge(row);
              let bustBadge = ''

              if (row.gap >= 50 && !row.debut) {
                const bustBadge = createBadge('badge-primary', 'Bustout', '≥50 shows on current tour since last played')
              }

              // Combine all active badges into one list, filtering out nulls
              const allBadges = [
                ...activeBadges,
                bustBadge,
                tourBadge
              ].filter(Boolean).join('');

              const badgeContainer = allBadges ? `<span class="ms-1">${allBadges}</span>` : '';
              const notes = row.notes ? `<span class="text-wrap fw-light setlist-note">${row.notes}</span>` : '';

              return `
                <div class="d-flex d-md-inline-flex justify-content-between justify-content-md-start align-items-center w-100">
                  ${songLink}${segue}
                  ${badgeContainer}
                </div>
                ${notes}
              `;
            }
          },
        ]

        // 2. FIXED Syntax: Return the native async promise chain directly.
        // 3. FIXED Reference: Pass the actual sandbox jQuery element ($sandboxTable) instead of '#setlistTable'
        return createTable(url, setlistColumns, $sandboxTable, setlistOptions)
          .then(() => {
            return new Promise((resolveRendering) => {
              resolveRendering(sandbox);
            });
          });
      })
      .then(sandbox => {
        const badgeRow = sandbox.querySelector('#badge-row');
        if (badgeRow) {
          badgeRow.style.maxWidth = '380px';
          badgeRow.style.marginLeft = 'auto';
          badgeRow.style.marginRight = 'auto';
        }

        const logoBrandLink = sandbox.querySelector('.navbar-brand');

        if (logoBrandLink) {
          // Wipe out Bootstrap float, margins, padding, and flex properties
          // logoBrandLink.className = '';

          // Force an explicit, centered block layout framework
          logoBrandLink.style.display = 'block';
          logoBrandLink.style.width = '100%';
          logoBrandLink.style.textAlign = 'center';
          logoBrandLink.style.paddingTop = '5px';
        }

        const targetCard = sandbox.querySelector('#capture-area') || sandbox.firstElementChild;
        const canvasBgColor = (config.activeTheme === 'dark') ? '#07080a' : '#ffffff'; // Match your dark background hex color

        // Hide the theme button from the image view, but keep it in the template code tree
        const themeToggle = sandbox.querySelector('#toggle-container, .bd-theme-btn');

        if (themeToggle) {
          themeToggle.style.setProperty('display', 'none', 'important');
        }

        const marginWrapper = document.createElement('div');
        marginWrapper.style.backgroundColor = canvasBgColor;
        marginWrapper.style.paddingBottom = '4px';
        marginWrapper.style.width = `${width}px`;

        targetCard.parentNode.insertBefore(marginWrapper, targetCard);
        marginWrapper.appendChild(targetCard);

        const captureArea = marginWrapper;

        if (!captureArea) {
          console.error("Capture area target '#capture-area' not found in sandbox.");
          sandbox.remove(); // Clean up memory
          return;
        }

        // 2. Fire Snapdom's native image exporter and download pipeline
        return snapdom.download(marginWrapper, {
          format: 'png',
          filename: `${config.downloadFilename}.png`,
          scale: 2,
          iconFonts: ['bootstrap-icons'], // Forces Snapdom to fetch and package the bootstrap-icon glyf data maps
          embedFonts: true // Forces style parsing from parent document head
        })
          .then(() => {
            // 3. Remove sandbox container after file compiles safely
            sandbox.remove();
          });
      })
      .catch(err => {
        console.error('Render pipeline crash:', err);
        alert('Could not compile table parameters.');
      })
      .finally(() => {
        button.disabled = false;
        button.innerHTML = originalText;
      });
  });
}
