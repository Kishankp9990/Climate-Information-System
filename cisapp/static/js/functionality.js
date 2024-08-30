
  // Initialize Leaflet map
  var map = L.map('map').setView([22, 84], 5); // Centered at [latitude, longitude], zoom level

  // Add a base tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, // Adjust maximum zoom level
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  // Optional: Add a marker to the map
  var marker = L.marker([32, 32]).addTo(map); // Marker at [latitude, longitude]
  marker.bindPopup("<br>Thi.").openPopup();
