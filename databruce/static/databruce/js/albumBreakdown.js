
// Helper utility function for escaping HTML
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function createSongListItem(song) {
  const display = song.original
    ? song.name
    : `${song.name} [${song.original_artist}]`;
  return `<li class="list-group-item px-1 py-0.5">${escapeHtml(display)}</li>`;
}

function createTooltipContent(item, tooltipSongs) {
  const categoryLabel = item.album_complete
    ? `${item.category} (Complete)`
    : item.category;
  return `<div class='text-start'><span class='text-xs'>${escapeHtml(categoryLabel)}</span><hr><span class='tooltip-songs'>${tooltipSongs}</span></div>`;
}

async function albumBreakdown(url) {
  if (!url || typeof url !== 'string') {
    throw new Error('Valid URL string is required');
  }

  const $albums = $('#albums');
  if (!$albums.length) {
    console.warn('Container #albums not found');
    return;
  }

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const { results } = await response.json();
    const tooltips = [];

    const maxNum = Math.max(...results.map(obj => obj.song_count));

    // Build HTML in memory to minimize DOM reflows
    for (const item of results) {
      const album = item.category_slug;
      const percent = ((item.song_count / maxNum) * 100).toFixed(0);
      const rowClass = item.album_complete
        ? "col px-2 py-1 album-breakdown complete"
        : "col px-2 py-1 album-breakdown";

      const songs = item.songs.map(createSongListItem).join('');

      const tooltipSongs = item.songs.map(song => {
        const artist = escapeHtml(song.original_artist);
        const songName = escapeHtml(song.name);
        return song.original
          ? `<span class='song'>${songName}</span>`
          : `<span class='song'>${songName}</span> <span class='artist'>[${artist}]</span>`;
      }).join('<br>');

      const tooltip = createTooltipContent(item, tooltipSongs);
      let albumArtUrl = `/static/databruce/img/albums/${album}.jpg`;

      if (album === 'originals' || album === 'covers') {
        albumArtUrl = '/static/databruce/img/albums/default.svg';
      }

      const html = `
        <div class="${rowClass}" data-bs-toggle="collapse" data-album="${album}" href="#${album}-collapse">
            <div class="row mx-0 g-3 align-items-center" data-bs-toggle="tooltip" data-bs-html="true" data-bs-title="${tooltip}">
                <div class="col-auto ps-0 category">
                    <img class="album-art" src="${albumArtUrl}" height="24" alt="${escapeHtml(item.category)}">
                </div>
                <div class="col progress px-0">
                    <div class="progress-bar" style="width:${percent}%"></div>
                </div>
                <div class="col-auto percent text-center pe-0 text-xs text-nowrap">${item.song_count}</div>
            </div>
            <div class="collapse" id="${album}-collapse">
                <ul class="list-group pt-2 pb-1">${songs}</ul>
            </div>
        </div>`;

      $albums.append(html);
    }

    // Initialize Tooltips
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
      tooltips.push(new bootstrap.Tooltip(el));
    });

    // Event delegation for hover effects
    const $setlistTable = $('#setlistTable');

    $albums.on('mouseenter', '.album-breakdown', function () {
      const album = $(this).data('album');
      $(this).css('cursor', 'pointer');

      $setlistTable.find('tbody tr:not(.set-header)').each(function () {
        const $tr = $(this);

        if ($tr.data('album') === album) {
          $tr.removeClass('opacity-25');
          $tr.children('td:not(.position)').addClass('highlighted');
        } else {
          $tr.addClass('opacity-25');
        }
      });
    }).on('mouseleave', '.album-breakdown', function () {
      $(`#setlistTable tr`).removeClass('opacity-25').children('td').removeClass('highlighted');
    });


    // Toggle album breakdown collapse elements
    $('#album-breakdown-btn').click(function () {
      const $collapses = $albums.find('.collapse');
      const anyClosed = $collapses.not('.show').length > 0;

      $collapses.each(function () {
        const bsCollapse = bootstrap.Collapse.getOrCreateInstance(this);
        anyClosed ? bsCollapse.show() : bsCollapse.hide();
      });
    });

    // Cleanup tooltips
    // return {
    //   destroy() {
    //     tooltips.forEach(t => t.dispose());
    //     $albums.off('mouseenter mouseleave').empty();
    //   }
    // };
  } catch (error) {
    console.error('Error fetching album breakdown:', error);
  }
}

