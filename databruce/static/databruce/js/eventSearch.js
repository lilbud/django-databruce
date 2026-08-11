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