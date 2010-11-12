// Global variables
var playerMarkers = new Array();

var reg = /(\d{4})(\d{2})(\d{2}) (\d{2}):(\d{2}):(\d{2})/; // !TODO!need to keep synced with mapmarkers format

function gotoPlayer(index)
{
    map.setCenter(playerMarkers[index].position);
    map.setZoom(config.markerZoom);
}

function delMarker(markername) {
    marker = playerMarkers[markername];
    
    if (marker) {
        marker.setVisible(false);
        //delete playerMarkers[markername];
        $('#plist span[name='+markername+']').remove();
        $('#plist br[name='+markername+']').remove();
    }
}

function prepareSignMarker(marker, item) {
      
      var c = "<div class=\"infoWindow\"><img src=\"signpost.png\" /><p>" + item.msg.replace(/\n/g,"<br/>") + "</p></div>";
      var infowindow = new google.maps.InfoWindow({
content: c
});
google.maps.event.addListener(marker, 'click', function() {
        infowindow.open(map,marker);
        });

}


function addMarker(item) {
    // Add marker if it doesnt exist
    // if it does, update position
		
		var m = reg.exec(item.timestamp),
			ts = new Date(m[1],m[2]-1,m[3],m[4],m[5],m[6]),
			d = new Date(),
			diff = d.getTime() - ts.getTime(),
			converted = fromWorldToLatLng(item.x, item.y, item.z);
		
		marker = playerMarkers[item.msg+item.id];
		
		
		// a default:
		var iconURL = 'smiley.gif';

		if (item.type == 'spawn') { iconURL = 'http://google-maps-icons.googlecode.com/files/home.png';}
		if (item.type == 'sign') { iconURL = 'signpost_icon.png';}

		

		
		
		if (marker) {
		    if (!marker.getVisible()) {
		        marker.setVisible(true);
		        if( diff < 10 * 1000*60 ) {
		            $('#plist').append("<span name='" + item.msg+item.id + "' onClick='gotoPlayer(\"" + item.msg+item.id + "\")'>" + item.msg + "</span><br name='" + item.msg+item.id + "' />");
		        }
		        else {
		            $('#plist').append("<span name='" + item.msg+item.id + "' onClick='gotoPlayer(\"" + item.msg+item.id + "\")' class='idle'>" + item.msg + "</span><br name='" + item.msg+item.id + "' />");
		        }
		    }
		    marker.setPosition(converted);
		}
		else {
		    if( diff < 10 * 1000*60 ) {
		        
		        var marker = new google.maps.Marker({
		                position: converted,
		                map: map,
		                title: item.msg,
		                icon: iconURL
		        });
		        $('#plist').append("<span name='" + item.msg+item.id + "' onClick='gotoPlayer(\"" + item.msg+item.id + "\")'>" + item.msg + "</span><br name='" + item.msg+item.id + "' />");
		        playerMarkers[item.msg+item.id] = marker;
		    }
		    else {
		        var marker = new google.maps.Marker({
		                position: converted,
		                map: map,
		                title: item.msg + " - Idle since " + ts.toString(),
		                icon: iconURL
		        });
		        $('#plist').append("<span name='" + item.msg+item.id + "' onClick='gotoPlayer(\"" + item.msg+item.id + "\")' class='idle'>" + item.msg + "</span><br name='" + item.msg+item.id + "' />");
		        playerMarkers[item.msg+item.id] = marker;
		    }
			
			if (item.type == 'sign') {
				prepareSignMarker(marker, item);
			}
		}
		
		
}


function refreshMarkers(){
    $.getJSON('markers.json', function(data) { //!Change to 'markers' if using cache.wsgi
            try {
                if (data == null || data.length == 0) {
                    $('#plist').html('[No players online]');
                    for (marker in playerMarkers) {
                        delMarker(marker);
                    }
                    return;
                }
                
                for (marker in playerMarkers) {
                    var found = false;
                    for (item in data) {
                        if (marker == data[item].msg + data[item].id)
                            found = true;
                        
                    }
                    if (!found) {
                        if (playerMarkers[marker].getVisible()) {
                            delMarker(marker);
                        }
                    }
                }
                
                if (data.length == 1 && $('#plist').text() == '[No players online]')
                    $('#plist').html('');
                
                for (item in data) {
                    if (data[item].id == 4)
                        addMarker(data[item]); // Only player markers, ignore other for now
                }
            }
            
            catch(err)
            {
                // Do nothing
            }
            
            
    });
    
}



function mapMarkersInit() {
    // initRegions(); //!TODO!Get MapRegions to write regions.json from cuboids
    
    
    var refreshInterval = setInterval(refreshMarkers, 3 * 1000);
    //refreshMarkers();
    
    
}


$(document).ready(function() {
        mapMarkersInit();
});
