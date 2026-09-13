function eventCard(event) {
  const badges = event.type.length > 0 ? event.type.map(
    (item) => `<span class="badge badge-${item.class} py-1 px-2"><span class="text-2xs">${item.name}</span></span>`
  ).join("") : "";

  var note_card = "";

  if (!event.note && !event.setlist.length) {
    note_card = `
        <div class="card message info mt-3">
          <span>
            We currently have no information available for this event. If you do, please <a class="text-reset fw-semibold" href="{% url "contact" %}">get in touch.</a>
          </span>
        </div>
    `
  } else if (!event.setlist.length && event.type[0].name != "No Gig") {
    note_card = `
    <hr>
        <div class="card message error mt-3">
          <span>No Setlist Known</span>
        </div>
    `
  }

  const setlistGroup = Object.groupBy(event.setlist, (item) => item.set_name);
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  if (Object.hasOwn(event, 'user_present') && event.public) {
    var form = `
    <form method="post"
        id="userForm"
        class="userForm d-flex align-items-center">
    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
    <button type="submit"
            class="btn btn-link p-0 border-0 text-xl bi ${event.user_present ? "bi-star-fill" : "bi-star"}"
            data-event="${event.id}"
            ${event.user_present ? "data-action='remove' data-attended='true'" : 'data-action="add" data-attended="false"'}
            id="add">
    </button>
    </form>
    `
  }

  let sets = "";

  Object.entries(setlistGroup).forEach(([key, value]) => {
    if (key == "Soundcheck") {
      var songs = value.map(song => {
        var songItem = `<span>${song.song}</span>`

        return song.segue ? `${songItem} /` : `${songItem}`
      }).join(" , ");

      songs = songs.replaceAll(" / ,", " > ");

      sets += `
      <div class="set-row text-xs">
        <span class="mb-1">${key}:</span>
        <span>${songs}</span>
      </div>
      `
    } else {
      var songs = value.map(song => {
        var songItem = (song.debut || song.premiere) ? `<span class="fw-semibold fst-italic text-primary">${song.song}</span>` : `<span>${song.song}</span>`

        return song.segue ? `${songItem} /` : `${songItem}`
      }).join(" , ");

      songs = songs.replaceAll(" / ,", " > ");

      sets += `
      <div class="set-row">
        <div class="text-muted text-xs mb-1 set-row-header">${key}:</div>
        <div class="song">
          ${songs}
        </div>
      </div>
      `
    }
  });

  const html = `
  <div class="col-12 event-card" id="${event.event_anchor}">
  <div class="card">
    <div class="card-body">
      <div class="header">
      <div class="row d-flex justify-content-between">
        <div class="col">
          ${badges ? `<div class="badges mb-2">${badges}</div>` : ""}
        </div>
        <div class="col-auto text-end" id="userPresent">
          ${form ? form : ""}
        </div>
      </div>
        <div class="title text-2xl row d-flex justify-content-between">
          <div class="col">
            <a href="/events/${event.event_id}" class="text-reset text-${event.type[0].class} fw-semibold">
              ${event.date} ${event.early_late ? `(${event.early_late})` : ""}
            </a>
          </div>
        </div>
        <div class="subtitle my-1">
          <div class="event-artist text-xl mb-1">${event.artist}</div>
          <div class="event-venue">
            <div class="venue-name text-base mb-0">${event.venue}</div>
            <div class="venue-city text-2xs text-muted d-flex gap-1"><i class="bi bi-geo-alt-fill"></i>${event.city}</div>
          </div>
        </div>
        
      </div>
        ${sets ? `<hr><div class="setlist row d-grid mt-2 mb-3 row-gap-2">${sets}</div>` : `${note_card}`}
        <div class="event-note">${event.note ? `<hr><div class="text-muted mb-1">Notes:</div>${event.event_note}` : ""}</div>
  </div>
</div>
  `

  return html
}