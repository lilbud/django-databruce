function renderCards(events) {
  const container = $('#cards');
  const fragment = $(document.createDocumentFragment());
  $(container).empty();

  events.forEach(function (item) {
    fragment.append(eventCard(item));
  })

  container.append(fragment);
}

function eventCard(event) {
  // Defensive: ensure required properties exist
  const badges = renderBadges(event.type ?? []);
  const noteCard = renderNoteCard(event);
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const attendanceForm = renderAttendanceForm(event, csrfToken);
  const setlistHtml = renderSetlist(event.setlist ?? []);
  const earlyLate = event.early_late ? `(${event.early_late})` : "";
  const cardBody = renderCardBody(setlistHtml, noteCard);

  return `
    <div class="col-12 event-card" id="${event.event_anchor}">
      <div class="card">
        ${renderCardHeader(event, badges, attendanceForm, earlyLate)}
        ${cardBody}
        ${renderCardFooter(event)}
      </div>
    </div>
  `;
}

function renderCardBody(setlist, note) {
  if (setlist || note) {
    return `
      <div class="card-body">
        ${setlist || note}
      </div>
    `;
  }

  return "";
}

// --- Helper Functions ---

function renderBadges(types) {
  if (!types?.length) return "";

  const badges = types
    .map(
      (item) => `
        <span class="badge badge-${item.class} py-1 px-2">
          <span class="text-2xs">${item.name}</span>
        </span>
      `
    )
    .join("");

  return `<div class="badges">${badges}</div>`;
}

function renderNoteCard(event) {
  const hasNote = Boolean(event.note);
  const hasSetlist = event.setlist?.length > 0;
  const firstTypeName = event.type?.[0]?.name;
  const blockedTypes = ["Rescheduled", "Cancelled", "Relocated", "No Gig"];

  if (!hasNote && !hasSetlist) {
    return `
      <div class="card message info">
        <span>
          We currently have no information available for this event. If you do, please
          <a class="text-reset fw-semibold" href="{% url 'contact' %}">get in touch.</a>
        </span>
      </div>
    `;
  }

  if (!hasSetlist && !blockedTypes.includes(firstTypeName)) {
    return `
      <div class="card message error">
        <span>No Setlist Known</span>
      </div>
    `;
  }

  return "";
}

function renderSetlist(setlist) {
  if (!setlist.length) return "";

  const grouped = Object.groupBy(setlist, (item) => item.set_name);

  const sets = Object.entries(grouped)
    .map(([setName, songs]) => renderSetSection(setName, songs))
    .join("");

  return `<div class="setlist row d-grid row-gap-2">${sets}</div>`;
}

function renderSetSection(setName, songs) {
  const isSoundcheck = setName === "Soundcheck";
  const songList = formatSongs(songs, !isSoundcheck);

  if (isSoundcheck) {
    return `
      <div class="set-row text-xs">
        <span class="mb-1">${setName}:</span>
        <span>${songList}</span>
      </div>
    `;
  }

  return `
    <div class="set-row">
      <div class="text-muted text-xs mb-1 set-row-header">${setName}:</div>
      <div class="song">${songList}</div>
    </div>
  `;
}

function formatSongs(songs, highlightSpecial) {
  const formatted = songs
    .map((song) => {
      let name = song.song;
      if (highlightSpecial && (song.debut || song.premiere)) {
        name = `<span class="fw-semibold fst-italic text-primary">${song.song}</span>`;
      } else {
        name = `<span>${song.song}</span>`;
      }
      return song.segue ? `${name} /` : name;
    })
    .join(" , ");

  // Replace " / ," with " > " for segues
  return formatted.replaceAll(" / ,", " > ");
}

function renderCardHeader(event, badges, attendanceForm, earlyLate) {
  const eventClass = event.type?.[0]?.class ?? "default";
  const titleHtml = event.title
    ? `<div class="event-title text-xs text-muted fst-italic my-1">${event.title}</div>`
    : "";
  const tourHtml = event.tour
    ? `<div class="event-tour text-xs text-muted my-1"><i class="bi bi-bus-front me-1"></i>${event.tour.name}</div>`
    : "";

  return `
    <div class="card-header">
      <div class="row mb-2 d-flex justify-content-between">
        <div class="col">${badges}</div>
        <div class="col-auto text-end text-xl" id="userPresent">${attendanceForm}</div>
      </div>
      
      <div class="title text-2xl row d-flex justify-content-between mb-1">
        <div class="col">
          <a href="/events/${event.event_id}" class="text-reset text-${eventClass} fw-semibold">
            ${event.date} ${earlyLate}
          </a>
        </div>
      </div>
      ${titleHtml}
      
      <div class="row event-artist text-xl mb-1">
        <div class="col">${event.artist.name}</div>
      </div>
      ${tourHtml}
      
      <div class="row event-venue">
        <div class="venue-name text-base">${event.venue ? event.venue.name : ""}</div>
        <div class="venue-city text-2xs text-muted d-flex gap-1">
          <i class="bi bi-geo-alt-fill"></i>${event.city}
        </div>
      </div>
    </div>
  `;
}

function renderCardFooter(event) {
  // BUG FIX: was using event.event_note instead of event.note
  const noteContent = event.event_note ? event.event_note : null;

  if (!noteContent) {
    return "";
  }

  return `
    <div class="card-footer">
      <div class="text-muted me-2">Notes:</div>
      ${noteContent}
    </div>
  `;
}