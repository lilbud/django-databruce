document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('venueContainer');

    // 1. Fetch data from your source
    fetch('/api/v1/venues?format=json') // Replace with your actual endpoint
        .then(response => response.json())
        .then(data => {
            console.log(data)
            // 2. Clear the 'Loading...' message
            container.innerHTML = '';

            // 3. Loop through data and create elements
            data.forEach(venue => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <div class="dropdown-item">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${venue.id}" id="v-${venue.id}">
                            <label class="form-check-label w-100" for="v-${venue.id}">
                                ${venue.formatted}
                            </label>
                        </div>
                    </div>
                `;
                container.appendChild(li);
            });
        })
        .catch(error => {
            container.innerHTML = '<li class="p-2 text-danger">Error loading data</li>';
            console.error('Error:', error);
        });
});

document.getElementById('venueSearch').addEventListener('keyup', function () {
    const filter = this.value.toLowerCase();
    const items = document.querySelectorAll('#venueContainer .dropdown-item');

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.closest('li').style.display = text.includes(filter) ? '' : 'none';
    });
});