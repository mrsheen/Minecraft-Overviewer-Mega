/**
 * The HomeControl adds a control to the map that simply
 * returns the user to Chicago. This constructor takes
 * the control DIV as an argument.
 */
function PlayerControl(controlDiv) {
 var controlUI = document.createElement('DIV');
 controlUI.id="players";
 controlUI.innerHTML = '<b><u>Online</u></b><p id="plist"></p>';
 controlDiv.appendChild(controlUI);
}

function StatusControl(controlDiv) {
 var controlUI = document.createElement('DIV');
 controlUI.id="info";
 controlUI.innerHTML = config.statusText;
 controlDiv.appendChild(controlUI);
}

function MapLinkControl(controlDiv) {
 var controlUI = document.createElement('DIV');
 controlUI.id="link";
 controlDiv.appendChild(controlUI);
}


 
function HomeControl(controlDiv, map) {
 
  controlDiv.style.padding = '5px';
 
  // Set CSS for the control border
  var controlUI = document.createElement('DIV');
  controlUI.className='controlUI';
  controlUI.title = 'Click to set the map to Spawn';
  controlDiv.appendChild(controlUI);
 
  // Set CSS for the control interior
  var controlText = document.createElement('DIV');
  controlText.className='controlText';
  controlText.innerHTML = '<b>Spawn</b>';
  controlUI.appendChild(controlText);
 
  // Setup the click event listeners: simply set the map to
  // Chicago
  google.maps.event.addDomListener(controlUI, 'click', function() {
    map.setCenter(config.mapCenter)
  });
 
}



function controls_init(){
// Create the DIV to hold the control and
  // call the HomeControl() constructor passing
  // in this DIV.
  var homeControlDiv = document.createElement('DIV');
  var homeControl = new HomeControl(homeControlDiv, map);
  
  var playerControlDiv = document.createElement('DIV');
  var playerControl = new PlayerControl(playerControlDiv);

  var statusControlDiv = document.createElement('DIV');
  var statusControl = new StatusControl(statusControlDiv);

  var mapLinkControlDiv = document.createElement('DIV');
  var mapLinkControl = new MapLinkControl(mapLinkControlDiv);
  
 
  homeControlDiv.index = 1;
  map.controls[google.maps.ControlPosition.TOP_RIGHT].push(homeControlDiv);
  map.controls[google.maps.ControlPosition.TOP_RIGHT].push(playerControlDiv);
  map.controls[google.maps.ControlPosition.BOTTOM_RIGHT].push(statusControlDiv);
  map.controls[google.maps.ControlPosition.BOTTOM_LEFT].push(mapLinkControlDiv);
}


$(document).ready(function() {
	
        setTimeout(controls_init,500);
});
