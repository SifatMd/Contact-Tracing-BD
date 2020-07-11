//power refresh to force changes made to js file: ctrl+F5

function singleid_ctrace(selected_uid, max_frequency, input_uid) {	
	  

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

  	rel_opacity = freq/max_freq;
  	if (rel_opacity < 0.1){ rel_opacity = 0.1}
  	else if (rel_opacity > 0.88) {rel_opacity = 0.88};

    if (exp_level == 3){
      // value_fillopacity = '#3ea383';
      // circle_color = '#1c9e75';
      value_fillopacity = '#35a4cc';
      circle_color = "#35a4cc";
      rad_factor = 1;
    }
    else if (exp_level == 2){
      // value_fillopacity = "#185f99";
      // circle_color = "#1208cc";
      value_fillopacity = '#e69007';
      circle_color = "#ff9d00";
      rad_factor = 1.15;
    }
    else if (exp_level == 1){
      // value_fillopacity = '#6c259c';
      // circle_color = "#4f0f94";
      value_fillopacity = '#6c259c';
      circle_color = "#4f0f94";
      rad_factor = 1.3;
    }

  	if (uid == input_uid){  
      	var circleref = L.circle([lat, long], {
      		color: 'red',
      		fillColor: "#e83535",
      		fillOpacity: rel_opacity,
      		radius: rad*1.4
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
      if (exp_level == 1){
        rad_factor = 1.3;
      }
      else if(exp_level == 2){
        rad_factor = 1.15;
      }
      else if(exp_level == 3){
        rad_factor = 1;
      }
  		var circleref = L.circle([lat, long], {
      		color: '#2db500',
      		fillColor: "#279e00",
      		fillOpacity: rel_opacity,
      		radius: rad*rad_factor
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
      		radius: rad*rad_factor
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














