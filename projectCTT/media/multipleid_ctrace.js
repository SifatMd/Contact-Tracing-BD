//power refresh to force changes made to js file: ctrl+F5

function multipleid_ctrace(selected_uid, max_frequency, input_uid) {	
	  

      map.removeLayer(group1);
      group1 = L.featureGroup();
      

      // google basemap
      L.tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{
      	attribution: 'BUET | Google Maps',
      	maxZoom:21,
      	subdomains:['mt0','mt1','mt2','mt3']
      }).addTo(map);

      
      //add scale to map
      // L.control.scale().addTo(map);
    var max_freq = max_frequency; 

  for (index=0; index < count_traj.length; index++){
  	lat = count_traj[index][0];
    long = count_traj[index][1];
    exp_level = count_traj[index][2];
    rad = count_traj[index][3];
    timespent = count_traj[index][4];
    uid = count_traj[index][5];
    freq = count_traj[index][6];

    puid = false;
    rel_opacity = freq/max_freq;
    if (rel_opacity < 0.1){ rel_opacity = 0.1}
    else if (rel_opacity > 0.88) {rel_opacity = 0.88};

    if (exp_level == 1){
      value_fillopacity = '#3ea383';
      circle_color = '#1c9e75';
    }
    else if (exp_level == 2){
      value_fillopacity = "#185f99";
      circle_color = "#1208cc";
    }
    else if (exp_level==3){
      value_fillopacity = '#6c259c';
      circle_color = "#4f0f94";
    }

    for (i1=0; i1 < input_uids.length; i1 ++) {
      if (uid == input_uids[i1]) {
        puid = true ;
        break;
      }
    }

    if (puid == true){ 
      var circleref = L.circle([lat, long], {
        color: 'red',
        fillColor: "#e83535",
        fillOpacity: rel_opacity,
        radius: rad*1.1
      }).addTo(group1);
      var strinfo = "ID: " + uid.toString() + " | Duration in Location: " + timespent.toString() + "hrs";
      var circlepopup = L.popup({offset:L.point(0,-5)}).setContent(strinfo);
      circleref.bindPopup(circlepopup);
      circleref.on('mouseover', function(evt){
        this.openPopup();
      })
      circleref.on('mouseout', function(evt){
        this.closePopup();
      })
    }
    else if (uid == selected_uid){
      var circleref = L.circle([lat, long], {
        color: '#e86f05',
        fillColor: "#e86f05",
        fillOpacity: rel_opacity,
        radius: rad
      }).addTo(group1);
      var strinfo = "ID: " + uid.toString() + " | Duration in Location: " + timespent.toString() + "hrs";
      var circlepopup = L.popup({offset:L.point(0,-5)}).setContent(strinfo);
      circleref.bindPopup(circlepopup);
      circleref.on('mouseover', function(evt){
        this.openPopup();
      })
      circleref.on('mouseout', function(evt){
        this.closePopup();
      })
    }
    else {
      var circleref = L.circle([lat, long], {
        color: circle_color,
        fillColor: value_fillopacity,
        fillOpacity: rel_opacity,
        radius: rad
      }).addTo(group1);
      var strinfo = "ID: " + uid.toString() + " | Duration in Location: " + timespent.toString() + "hrs";
      var circlepopup = L.popup({offset:L.point(0,-5)}).setContent(strinfo);
      circleref.bindPopup(circlepopup);
      circleref.on('mouseover', function(evt){
        this.openPopup();
      })
      circleref.on('mouseout', function(evt){
        this.closePopup();
      })
    }

  }
  map.addLayer(group1);
  // function getColor(d){ 
  // 		return d == 0 ? '#db2727':
  // 				d == 1 ? '#1e83f7':
  // 						'#4fb514';
  // }
  // //add legends
  // var legend = L.control({position: 'topright'});
  // legend.onAdd = function(map){
  // 	var div = L.DomUtil.create('div','info legend'),
  // 	grades = ["Covid Positive", "Contacted Persons"];
  	
  // 	//style of i: width:18px;height:18px;float:left;opacity:0.7;
  // 	div.innerHTML += '<i style="width:16px;height:16px;float:left;opacity:0.7;background:' + getColor(0) + ';"></i>' + grades[0] + '<br>';
  // 	div.innerHTML += '<i style="width:16px;height:16px;float:left;opacity:0.7;background:' + getColor(1) + ';"></i>' + grades[1];
  // 	return div;
  //  };
  //  legend.addTo(map);

}














