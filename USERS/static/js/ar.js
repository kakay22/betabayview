let scene, camera, renderer, arrowMesh;

function navigateToVisit(requestId) {
    const lat = 10.123; // replace with the actual latitude from your request
    const lng = 20.123; // replace with the actual longitude from your request

    // Initialize Three.js scene
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    scene.add(camera);
    
    // Set up the AR renderer
    renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('arContainer').appendChild(renderer.domElement);
    
    // Create the blue arrow
    const arrowGeometry = new THREE.ConeGeometry(0.1, 1, 32);
    const arrowMaterial = new THREE.MeshBasicMaterial({ color: 0x0000ff });
    arrowMesh = new THREE.Mesh(arrowGeometry, arrowMaterial);
    scene.add(arrowMesh);

    // Get device orientation and location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;

            // Calculate the direction vector to the target location
            const targetPosition = calculateDirection(userLat, userLng, lat, lng);
            arrowMesh.position.set(targetPosition.x, targetPosition.y, targetPosition.z);
            arrowMesh.lookAt(new THREE.Vector3(0, 0, 0)); // Point the arrow towards the origin

            // Set the camera position to the user's location (optional)
            camera.position.set(targetPosition.x, targetPosition.y + 1, targetPosition.z + 5); // Elevate the camera
        });
    } else {
        alert('Geolocation is not supported by this browser.');
    }

    // Start the AR experience
    initAR();
}

function initAR() {
    // Create a basic AR.js scene
    const arScene = document.createElement('a-scene');
    arScene.setAttribute('embedded', '');
    arScene.setAttribute('arjs', 'sourceType: webcam;');
    
    const arrowEntity = document.createElement('a-entity');
    arrowEntity.setAttribute('geometry', 'primitive: cone; radiusBottom: 0.1; height: 1;');
    arrowEntity.setAttribute('material', 'color: blue;');
    arrowEntity.setAttribute('position', `${arrowMesh.position.x} ${arrowMesh.position.y} ${arrowMesh.position.z}`);
    
    arScene.appendChild(arrowEntity);
    document.getElementById('arContainer').appendChild(arScene);

    // Start rendering
    animate();
}

function calculateDirection(userLat, userLng, targetLat, targetLng) {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (targetLat - userLat) * (Math.PI / 180);
    const dLng = (targetLng - userLng) * (Math.PI / 180);
    
    // Calculate distance
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(userLat * (Math.PI / 180)) * Math.cos(targetLat * (Math.PI / 180)) *
              Math.sin(dLng / 2) * Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c; // Distance in kilometers

    // Convert distance to a 3D vector (this is a simplification)
    const heightOffset = 0; // Adjust this for elevation
    return {
        x: distance * Math.cos(dLat) * Math.cos(dLng),
        y: heightOffset,
        z: distance * Math.cos(dLat) * Math.sin(dLng)
    };
}

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
