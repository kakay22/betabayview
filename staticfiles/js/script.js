// Example of custom JavaScript code

// Function to log a message when the scene is loaded
document.addEventListener('DOMContentLoaded', function() {
	console.log('The AR scene has been loaded.');
  });
  
  // Function to interact with 3D objects in the scene
  function setupScene() {
	// Get the 3D objects
	const box = document.querySelector('#box');
	const sphere = document.querySelector('#sphere');
  
	// Modify the box color after 2 seconds
	setTimeout(() => {
	  box.setAttribute('color', 'green');
	}, 2000);
  
	// Rotate the sphere continuously
	function animateSphere() {
	  const rotation = sphere.getAttribute('rotation');
	  sphere.setAttribute('rotation', {
		x: rotation.x,
		y: rotation.y + 1,
		z: rotation.z
	  });
	  requestAnimationFrame(animateSphere);
	}
	animateSphere();
  }
  
  // Initialize the scene setup
  setupScene();
  