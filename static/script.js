document.addEventListener('DOMContentLoaded', () => {
    const photoInput = document.getElementById('photo-input');
    const metadataContainer = document.getElementById('metadata-container');

    photoInput.addEventListener('change', () => {
        const file = photoInput.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('photo', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                metadataContainer.innerHTML = '';
                if (data.error) {
                    metadataContainer.innerHTML = `<p>Error: ${data.error}</p>`;
                } else {
                    const table = document.createElement('table');
                    const tbody = document.createElement('tbody');

                    for (const key in data) {
                        const row = document.createElement('tr');
                        const keyCell = document.createElement('td');
                        const valueCell = document.createElement('td');
                        keyCell.textContent = key;
                        valueCell.textContent = data[key];
                        row.appendChild(keyCell);
                        row.appendChild(valueCell);
                        tbody.appendChild(row);
                    }

                    table.appendChild(tbody);
                    metadataContainer.appendChild(table);
                }
            })
            .catch(error => {
                metadataContainer.innerHTML = `<p>An error occurred: ${error}</p>`;
            });
        }
    });
});
