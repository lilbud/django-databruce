myModal.addEventListener('shown.bs.modal', function () {
  const myInput = document.getElementById('eventSearch');
  myInput.focus();
});

$("form").on("keydown", "input:not(textarea)", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
});

$('#eventSearch').on('input', function () {
  const query = $(this).val();

  // If the query is a date, format to YYYY-MM-DD
  if (/^\d/.test(query)) {
    let numbersOnly = query.replace(/\D/g, '');
    let formatted = '';

    if (numbersOnly.length > 0) formatted += numbersOnly.substring(0, 4);
    if (numbersOnly.length > 4) formatted += '-' + numbersOnly.substring(4, 6);
    if (numbersOnly.length >= 6) formatted += '-' + numbersOnly.substring(6, 8);
    $(this).val(formatted);
  }

  clearTimeout(searchTimer);

  // Wait 500 milliseconds before calling the function
  searchTimer = setTimeout(function () {
    eventSearch(query);
  }, 500);
});

function eventSearch(query) {
  // Clear the previous results
  results.innerHTML = '';
  $('#results').hide();

  // Only trigger search if input longer than 4 characters
  if (query.length >= 4) {
    // Show spinner
    $("#loadingContainer").show();

    fetch(`/api/v1/events/?search=${query}`)
      .then(response => response.json())
      .then(data => {
        // Loop and append results
        data.results.forEach(element => {
          $(results).append(
            `<a href="/events/${element.event_id}" class="list-group-item">
                  ${element.date}<br>${element.venue.name} - ${element.artist.name}
                </a>`
          );
        });

        // show results
        $(results).show();
      })
      .catch(error => console.error('Error:', error))
      .finally(() => {
        // Hide the spinner when done, even if the request fails
        $("#loadingContainer").hide();
      });

  } else {
    // If the query is too short, ensure the spinner stays hidden
    $("#loadingContainer").hide();
  }
}