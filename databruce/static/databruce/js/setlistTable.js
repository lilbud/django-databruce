const createBadge = (cls, text, title) =>
  `<span class="badge ${cls} align-middle ms-1" data-bs-toggle="tooltip" data-bs-html="true" data-bs-title="${title}">${text}</span>`;

const SONG_BADGES = [
  { key: 'instrumental', class: 'badge-info', label: 'Inst.', title: 'Instrumental' },
  { key: 'sign_request', class: 'badge-info', label: 'Sign', title: 'Sign Request' },
  { key: 'nobruce', class: 'badge-warning', label: 'No Boss', title: 'Song Played Without Bruce' },
  { key: 'debut', class: 'badge-primary d-inline-block d-md-none d-lg-none', label: 'Tour Debut', title: 'Tour Debut' },
  { key: 'premiere', class: 'badge-secondary d-inline-block d-md-none d-lg-none', label: 'First', title: 'First Time Played' },
];

function getTourPositionBadge(row) {
  const { tour_num: num, tour_total: total } = row;

  if (num && total && num === total) {
    return total === 1
      ? createBadge('badge-secondary d-inline-block d-md-none d-lg-none', 'Tour Only', 'Only Tour Performance')
      : createBadge('badge-warning d-inline-block d-md-none d-lg-none', `Tour Last`, `Final Tour Performance<br>(${num}/${total})`);
  }
  return null;
}