async function initializeShareCardGenerator(config) {
  const button = config.button;
  const originalText = button.innerHTML;
  const width = 540;
  let sandbox = null;

  button.disabled = true;
  button.innerHTML = '<span class="spinner-border spinner-border-sm py-auto" role="status"></span> Generating Image...';

  await fetch(config.shareCardUrl)
    .then(response => {
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return response.text();
    })
    .then(htmlContent => {
      sandbox = document.createElement('div');

      sandbox.style.position = 'fixed';
      sandbox.style.top = '-9999px';
      sandbox.style.left = '-9999px';
      sandbox.style.width = `${width}px`;

      sandbox.setAttribute('data-bs-theme', config.activeTheme === 'dark' ? 'dark' : 'light');

      sandbox.innerHTML = htmlContent;
      document.body.appendChild(sandbox);

      // ensure badges wrap instead of overflow
      const badgeRow = sandbox.querySelector('#badge-row');
      if (badgeRow) {
        badgeRow.style.maxWidth = '380px';
        badgeRow.style.marginLeft = 'auto';
        badgeRow.style.marginRight = 'auto';
      }

      // segue arrows misaligned on image
      const arrows = sandbox.querySelectorAll('span.segue');

      if (arrows) {
        arrows.forEach(arrow => {
          arrow.style.marginTop = '-28px';
        });
      }

      // Force eager loading and wait for all images in sandbox
      const images = Array.from(sandbox.querySelectorAll('img'));
      const imagePromises = images.map(img => {
        img.loading = 'eager';
        img.decoding = 'sync';

        if (img.complete && img.naturalWidth > 0) {
          return img.decode().catch(() => { });
        }
        return new Promise(resolve => {
          img.addEventListener('load', () => img.decode().then(resolve).catch(resolve), { once: true });
          img.addEventListener('error', resolve, { once: true });
        });
      });

      return Promise.all(imagePromises).then(() => sandbox);

    }).then(sandbox => {
      const targetCard = sandbox.querySelector('#capture-area') || sandbox.firstElementChild;
      if (!targetCard) {
        throw new Error("Capture area target '#capture-area' not found in sandbox.");
      }

      const canvasBgColor = (config.activeTheme === 'dark') ? '#07080a' : '#ffffff';

      const marginWrapper = document.createElement('div');
      marginWrapper.style.backgroundColor = canvasBgColor;
      marginWrapper.style.paddingBottom = '4px';
      marginWrapper.style.width = `${width}px`;

      targetCard.parentNode.insertBefore(marginWrapper, targetCard);
      marginWrapper.appendChild(targetCard);

      return snapdom.download(marginWrapper, {
        format: 'png',
        filename: `${config.downloadFilename}.png`,
        scale: 2,
        iconFonts: ['bootstrap-icons'],
        embedFonts: true
      });
    })
    .catch(err => {
      console.error('Render pipeline crash:', err);
      alert('Could not generate share image.');
    })
    .finally(() => {
      if (sandbox) sandbox.remove();
      button.disabled = false;
      button.innerHTML = originalText;
    });
}

// function initializeShareCardGenerator(config) {
//   const button = config.button;
//   const originalText = button.innerHTML;
//   const width = 540;
//   const url = config.ajaxUrl;

//   button.disabled = true;
//   button.innerHTML = '<span class="spinner-border spinner-border-sm py-auto" role="status"></span> Generating Image...';

//   const fetchUrl = new URL(window.location.href);
//   fetchUrl.searchParams.set('share_card', '1');

//   fetch(config.shareCardUrl, {
//     cache: 'no-store',
//   })
//     .then(response => response.text())
//     .then(htmlContent => {
//       const sandbox = document.createElement('div');

//       // sandbox.style.position = 'fixed';
//       // sandbox.style.top = '-9999px';
//       // sandbox.style.left = '-9999px';
//       // sandbox.style.width = `${width}px`;

//       sandbox.innerHTML = htmlContent;
//       document.body.appendChild(sandbox);

//       // const $sandboxTable = sandbox.querySelector('#setlistTable');

//       // if (config.activeTheme === 'dark') {
//       //   sandbox.setAttribute('data-bs-theme', 'dark');
//       // } else {
//       //   sandbox.setAttribute('data-bs-theme', 'light');
//       // }

//       // let setlistOptions = {
//       //   createdRow: function (row, data) {
//       //     row.className = slugify(data.set_name);
//       //     return row
//       //   },
//       //   rowGroup: {
//       //     groupVal: 'set_name'
//       //   }
//       // }

//       // let setlistColumns = [
//       //   {
//       //     'data': 'song_num',
//       //     'className': 'text-center',
//       //     'width': '',
//       //     'render': function (data, type, row, meta) {
//       //       return data ? data : '';
//       //     },
//       //     'createdCell': function (td, cellData, rowData, row, col) {
//       //       td.classList.add('songnum');

//       //       if (rowData.position) {
//       //         var position = slugify(rowData.position);
//       //         td.classList.add(position, 'position');
//       //       }

//       //       return td;
//       //     },
//       //   },
//       //   {
//       //     'data': 'song',
//       //     'className': 'text-wrap',
//       //     'width': '',
//       //     'render': function (data, type, row, meta) {
//       //       const songLink = `<a class="text-reset" href="/songs/${data.slug}">${data.name}</a>`;
//       //       const segue = row.segue ? ' <span class="segue"></span>' : '';

//       //       const activeBadges = SONG_BADGES
//       //         .filter(b => row[b.key])
//       //         .map(b => createBadge(b.class, b.label, b.title))

//       //       const tourBadge = getTourPositionBadge(row);
//       //       let bustBadge = ''

//       //       // Combine all active badges into one list, filtering out nulls
//       //       const allBadges = [
//       //         ...activeBadges,
//       //         bustBadge,
//       //         tourBadge
//       //       ].filter(Boolean).join('');

//       //       const badgeContainer = allBadges ? `<span class="ms-1">${allBadges}</span>` : '';
//       //       const notes = row.notes ? `<span class="text-wrap fw-light setlist-note">${row.notes}</span>` : '';

//       //       return `
//       //           <div class="d-flex d-md-inline-flex justify-content-between justify-content-md-start align-items-center w-100">
//       //             ${songLink}${segue}
//       //             ${badgeContainer}
//       //           </div>
//       //           ${notes}
//       //         `;
//       //     }
//       //   },
//       // ]

//       return createTable(url, setlistColumns, $sandboxTable, setlistOptions)
//         .then(() => {
//           return new Promise((resolveRendering) => {
//             resolveRendering(sandbox);
//           });
//         });
//     })
//     .then(async sandbox => {
//       const badgeRow = sandbox.querySelector('#badge-row');
//       if (badgeRow) {
//         badgeRow.style.maxWidth = '380px';
//         badgeRow.style.marginLeft = 'auto';
//         badgeRow.style.marginRight = 'auto';
//       }

//       const arrows = sandbox.querySelectorAll('span.segue');

//       if (arrows) {
//         arrows.forEach(arrow => {
//           arrow.style.marginTop = '-28px';
//         });
//       }

//       const targetCard = sandbox.querySelector('#capture-area') || sandbox.firstElementChild;
//       const canvasBgColor = (config.activeTheme === 'dark') ? '#07080a' : '#ffffff'; // Match your dark background hex color

//       // Hide the theme button from the image view, but keep it in the template code tree
//       const themeToggle = sandbox.querySelector('#toggle-container, .bd-theme-btn');

//       if (themeToggle) {
//         themeToggle.style.setProperty('display', 'none', 'important');
//       }

//       const marginWrapper = document.createElement('div');
//       marginWrapper.style.backgroundColor = canvasBgColor;
//       marginWrapper.style.paddingBottom = '4px';
//       marginWrapper.style.width = `${width}px`;

//       targetCard.parentNode.insertBefore(marginWrapper, targetCard);
//       marginWrapper.appendChild(targetCard);

//       const captureArea = marginWrapper;

//       if (!captureArea) {
//         console.error("Capture area target '#capture-area' not found in sandbox.");
//         sandbox.remove(); // Clean up memory
//         return;
//       }

//       // 2. Fire Snapdom's native image exporter and download pipeline
//       return snapdom.download(marginWrapper, {
//         format: 'png',
//         filename: `${config.downloadFilename}.png`,
//         scale: 2,
//         iconFonts: ['bootstrap-icons'], // Forces Snapdom to fetch and package the bootstrap-icon glyf data maps
//         embedFonts: true // Forces style parsing from parent document head
//       })
//         .then(() => {
//           // 3. Remove sandbox container after file compiles safely
//           sandbox.remove();
//         });
//     })
//     .catch(err => {
//       console.error('Render pipeline crash:', err);
//       alert('Could not compile table parameters.');
//     })
//     .finally(() => {
//       if (sandbox) sandbox.remove();
//       button.disabled = false;
//       button.innerHTML = originalText;
//     });
// }
