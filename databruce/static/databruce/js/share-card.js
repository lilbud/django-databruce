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

        return new Promise((resolve) => {
          $sandboxTable.DataTable({
            ajax: config.ajaxUrl, // <-- Loaded dynamically from config
            layout: config.layout,
            serverSide: true,
            processing: true,
            paging: false,
            ordering: false,
            searching: false,
            info: false,
            scrollX: false,
            fixedHeader: false,
            autoWidth: false,
            rowGroup: {
              dataSrc: 'set_name',
              className: 'text-center set-header p-0 dtrg-group',
              startRender: function (rows, group) {
                const g = `<span>${group}</span>`;
                const td = `<td colspan="${rows.columns().count()}" class="py-0">${g}</td>`;
                return $('<tr />').addClass(slugify(group)).append(td);
              }
            },
            createdRow: function (row, data, dataIndex) {
              $(row).addClass(slugify(data.set_name));

              var allowedSets = ['Show', 'Set 1', "Set 2", 'Encore', 'Pre-Show', 'Post-Show', 'Rehearsal']

              if (allowedSets.includes(data.set_name) && data.song) {
                var album = data.song.category_slug;
                $(row).attr('album', album);
              }
            },
            columnDefs: [
              { 'targets': '_all', columnControl: [] }
            ],
            columns: [
              {
                'data': 'song_num',
                'className': 'dt-center col-songnum',
                'width': '30px',
                'render': function (data, type, row, meta) {
                  if (type === 'display' && data) {
                    return data;
                  }
                },
                'createdCell': function (td, cellData, rowData, row, col) {
                  $(td).addClass('songnum');

                  if (rowData.position) {
                    var position = slugify(rowData.position);
                    $(td).addClass(`${position} position`).attr('data-bs-toggle', 'tooltip').attr('data-bs-title', rowData.position)
                  }

                  return td;
                },
              },
              {
                'data': 'song',
                'name': 'song__sort_song_name',
                'className': 'text-wrap col-song',
                'render': function (data, type, row, meta) {
                  if (type === 'display' && data) {
                    var song = `<a class="text-reset" href="/songs/${data.uuid}">${data.name}</a>`;
                    var segue = row.segue ? `<span class="segue"></span>` : '';

                    song = `${song} ${segue}`;

                    var badges = $('<span />').addClass('ms-2 d-inline-flex gap-1');
                    var baseBadge = `<span class="badge"></span>`

                    if (row.instrumental) {
                      var badge = $(baseBadge).clone();
                      $(badge).addClass('badge-info').text('Instrumental');
                      badges.append($(badge).prop('outerHTML'));
                    }

                    if (row.sign_request) {
                      var badge = $(baseBadge).clone();
                      $(badge).addClass('badge-info').text('Sign Request');
                      $(badges).append($(badge).prop('outerHTML'));
                    }

                    if (row.nobruce) {
                      var badge = $(baseBadge).clone();
                      $(badge).addClass('badge-warning').text('No Boss');
                      $(badges).append($(badge).prop('outerHTML'));
                    }

                    if (row.last == 0) {
                      gap = null;
                    } else {
                      gap = row.last;
                    }

                    var debut = row.debut;
                    var premiere = row.premiere;

                    if (premiere) {
                      var badge = $(baseBadge).clone();
                      $(badge).addClass('badge-secondary').text(`First`);
                      $(badges).append($(badge).prop('outerHTML'));
                    }

                    if (debut) {
                      var badge = $(baseBadge).clone();
                      $(badge).addClass('badge-primary').text(`Tour Debut`);
                      $(badges).append($(badge).prop('outerHTML'));
                    }

                    if (row.notes) {
                      var notes = `<span class="text-wrap d-inline-block fw-light setlist-note">${row.notes}</span>`;
                      return badges ? song + $(badges).prop('outerHTML') + '<br>' + notes : song;
                    }

                    return badges ? song + $(badges).prop('outerHTML') : song;
                  }
                },
              },
            ],

            initComplete: function () {
              // Badge wrap fix
              const badgeRow = sandbox.querySelector('#badge-row');
              if (badgeRow) {
                badgeRow.style.maxWidth = '320px';
                badgeRow.style.marginLeft = 'auto';
                badgeRow.style.marginRight = 'auto';
              }

              // Font alignment fix
              const badges = sandbox.querySelectorAll('.badge-row span.badge');
              badges.forEach(badge => {
                const textContent = badge.textContent.trim();
                badge.innerHTML = `
                                <span style="
                                    display: inline-block;
                                    line-height: 1 !important;
                                    vertical-align: middle;
                                    position: relative;
                                    top: -1.5px;
                                ">${textContent}</span>
                            `;
              });

              setTimeout(() => resolve(sandbox), 50);
            }
          });
        });
      })
      .then(sandbox => {
        const logoBrandLink = sandbox.querySelector('.navbar-brand-mobile');
        if (logoBrandLink) {
          // Wipe out Bootstrap float, margins, padding, and flex properties
          // logoBrandLink.className = '';

          // Force an explicit, centered block layout framework
          logoBrandLink.style.display = 'block';
          logoBrandLink.style.width = '100%';
          logoBrandLink.style.textAlign = 'center';
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
        marginWrapper.style.paddingTop = '0';
        marginWrapper.style.paddingBottom = '12px';
        marginWrapper.style.width = `${width}px`;

        targetCard.parentNode.insertBefore(marginWrapper, targetCard);
        marginWrapper.appendChild(targetCard);

        const totalRect = marginWrapper.getBoundingClientRect();

        const options = {
          scale: 2,
          useCORS: true,
          backgroundColor: canvasBgColor,
          scrollX: 0,
          letterRendering: true,
          scrollY: 0,
          x: 0,
          y: 0,
          width: width,
          height: totalRect.height
        };

        return html2canvas(marginWrapper, options).then(canvas => {
          const imageURL = canvas.toDataURL('image/png');
          const downloadLink = document.createElement('a');
          downloadLink.href = imageURL;
          downloadLink.download = `${config.downloadFilename}.png`;

          document.body.appendChild(downloadLink);
          downloadLink.click();
          document.body.removeChild(downloadLink);
          document.body.removeChild(sandbox);
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
