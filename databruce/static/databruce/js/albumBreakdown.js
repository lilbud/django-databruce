function createSongListItem(song) {
  const display = song.original
    ? song.name
    : `${song.name} [${song.original_artist}]`;
  return `<li class="list-group-item px-1 py-0.5">${escapeHtml(display)}</li>`;
}

function createTooltipContent(item, tooltipSongs) {
  const categoryLabel = item.album_complete
    ? `${item.category.name} (Complete)`
    : item.category.name;
  return `<div class='text-start'><span class='text-xs'>${escapeHtml(categoryLabel)}</span><hr><span class='tooltip-songs'>${tooltipSongs}</span></div>`;
}

async function albumBreakdown(url) {
  if (!url || typeof url !== 'string') {
    throw new Error('Valid URL string is required');
  }

  const albums = document.getElementById('albums');

  if (!albums) {
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

    // const maxNum = Math.max(...results.map(obj => obj.song_count));

    const maxLength = Object.values(results).reduce((max, item) => {
      return Math.max(max, item.songs?.length || 0);
    }, 0);

    console.log(maxLength);

    // Build HTML in memory to minimize DOM reflows
    for (const item of results) {
      const album = item.category;
      const percent = ((item.songs.length / maxLength) * 100).toFixed(0);
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
      let albumArtUrl = `/static/databruce/img/albums/${album.slug}.jpg`;

      if (album.slug === 'originals' || album.slug === 'covers') {
        albumArtUrl = '/static/databruce/img/albums/default.svg';
      }

      const html = `
        <div class="${rowClass}" data-bs-toggle="collapse" data-album="${album.id}" href="#row-${album.id}-collapse" id="row-${album.id}">
            <div class="row mx-0 g-3 align-items-center" data-bs-toggle="tooltip" data-bs-html="true" data-bs-title="${tooltip}">
                <div class="col-auto ps-0 category">
                    <img class="album-art" src="${albumArtUrl}" height="24" alt="${escapeHtml(item.category.name)}">
                </div>
                <div class="col progress px-0">
                    <div class="progress-bar" style="width:${percent}%"></div>
                </div>
                <div class="col-auto percent text-center pe-0 text-xs text-nowrap">${item.songs.length}</div>
            </div>
            <div class="collapse" id="row-${album.id}-collapse">
                <ul class="list-group pt-2 pb-1">${songs}</ul>
            </div>
        </div>`;

      albums.insertAdjacentHTML('beforeend', html);
    }

    // Initialize Tooltips
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
      tooltips.push(new bootstrap.Tooltip(el));
    });

    const setlistTable = document.getElementById('setlistTable');

    // Assuming 'albums' is a vanilla DOM element
    albums.addEventListener('mouseover', function (e) {
      const breakdown = e.target.closest('.album-breakdown');
      if (!breakdown) return;

      const album = breakdown.dataset.album;
      breakdown.style.cursor = 'pointer';

      const rows = setlistTable.querySelectorAll('tbody tr:not(.set-header)');
      rows.forEach(tr => {
        if (tr.dataset.album === album) {
          tr.classList.remove('opacity-25');
          tr.querySelectorAll('td:not(.position)').forEach(td => td.classList.add('highlighted'));
        } else {
          tr.classList.add('opacity-25');
        }
      });
    });

    albums.addEventListener('mouseout', function (e) {
      const breakdown = e.target.closest('.album-breakdown');
      if (!breakdown) return;

      const allRows = setlistTable.querySelectorAll('tr');
      allRows.forEach(tr => {
        tr.classList.remove('opacity-25');
        tr.querySelectorAll('td').forEach(td => td.classList.remove('highlighted'));
      });
    });
  } catch (error) {
    console.error('Error fetching album breakdown:', error);
  }
}

