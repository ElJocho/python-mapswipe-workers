const BUILD_AREA_TYPE = 1
const FOOTPRINT_TYPE = 2
const CHANGE_DETECTION_TYPE = 3
const COMPLETENESS_TYPE = 4

//auto expand textarea
function adjust_textarea(h) {
    h.style.height = "20px";
    h.style.height = (h.scrollHeight)+"px";
}

function initForm() {
    initMap();
    initTeams();
    displayProjectTypeForm("build_area")
}


function initMap() {
  ProjectAoiMap = L.map('geometryMap').setView([0.0, 0.0], 4);
  L.tileLayer( 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    subdomains: ['a','b','c']
  }).addTo( ProjectAoiMap );
  console.log('added map');
  aoiLayer = L.geoJSON().addTo(ProjectAoiMap);
  setTimeout(function(){ ProjectAoiMap.invalidateSize()}, 400);

  }


function initTeams() {
    console.log("init teams")
    // get teams from firebase
    var TeamsRef = firebase.database().ref("v2/teams").orderByChild("teamName");
    TeamsRef.once('value', function(snapshot){
    if(snapshot.exists()){
        snapshot.forEach(function(data){
            // add teamName to drop down option and set teamId as value
            option = document.createElement('option')
            option.innerHTML = data.val().teamName
            option.value = data.key
            document.getElementById("visibility").appendChild(option);
            })
        }
    })
}


function initTutorials(projectType) {
    // clear all existing options
    document.getElementById("tutorial").innerHTML = ""
    console.log("init tutorials")
    // get teams from firebase
    var TutorialsRef = firebase.database().ref("v2/projects").orderByChild("status").equalTo("tutorial");
    TutorialsRef.once('value', function(snapshot){
    if(snapshot.exists()){
        snapshot.forEach(function(data){
            // add teamName to drop down option and set teamId as value
            if (data.val().projectType == projectType) {
                option = document.createElement('option')
                option.innerHTML = data.val().name
                option.value = data.key
                document.getElementById("tutorial").appendChild(option);
                }
            })
        }
    })
}


function displayProjectTypeForm(projectType) {
    document.getElementById("projectType").value = projectType;
    switch (projectType) {
        case "build_area":
            initTutorials(BUILD_AREA_TYPE);
            displayTileServer("bing", "A");
            document.getElementById("groupSize").value = 120;
            document.getElementById("form_project_aoi_geometry").style.display = "block";
            document.getElementById("form_project_task_geometry").style.display = "None";
            document.getElementById("form_zoom_level").style.display = "block";
            document.getElementById("form_tile_server_a").style.display = "block";
            document.getElementById("form_tile_server_b").style.display = "None";
            setTimeout(function(){ ProjectAoiMap.invalidateSize()}, 400);
            document.getElementById("form_team_settings").style.display = "None";
            break;
        case "footprint":
            initTutorials(FOOTPRINT_TYPE);
            displayTileServer("bing", "A");
            document.getElementById("groupSize").value = 25;
            document.getElementById("form_project_aoi_geometry").style.display = "None";
            document.getElementById("form_project_task_geometry").style.display = "block";
            document.getElementById("form_zoom_level").style.display = "None";
            document.getElementById("form_tile_server_a").style.display = "block";
            document.getElementById("form_tile_server_b").style.display = "None";
            document.getElementById("form_team_settings").style.display = "None";
            break;
        case "change_detection":
        case "completeness":
            displayTileServer("bing", "A");
            displayTileServer("bing", "B");
            if (projectType == "change_detection") {
                document.getElementById("groupSize").value = 25;
                initTutorials(CHANGE_DETECTION_TYPE);
            } else {
                document.getElementById("groupSize").value = 80;
                initTutorials(COMPLETENESS_TYPE);
            }
            document.getElementById("form_project_aoi_geometry").style.display = "block";
            document.getElementById("form_project_task_geometry").style.display = "None";
            document.getElementById("form_zoom_level").style.display = "block";
            document.getElementById("form_tile_server_a").style.display = "block";
            document.getElementById("form_tile_server_b").style.display = "block";
            setTimeout(function(){ ProjectAoiMap.invalidateSize()}, 400);
            document.getElementById("form_team_settings").style.display = "None";
            break;
    }
}

function addTileServerCredits (tileServerName, which) {
    var credits = {
        "bing": "© 2019 Microsoft Corporation, Earthstar Geographics SIO",
        "maxar_premium": "© 2019 Maxar",
        "maxar_standard": "© 2019 Maxar",
        "esri": "© 2019 ESRI",
        "esri_beta": "© 2019 ESRI",
        "mapbox": "© 2019 MapBox",
        "sinergise": "© 2019 Sinergise",
        "custom": "Please add imagery credits here."
    }
    document.getElementById("tileServer"+which+"Credits").value = credits[tileServerName]
}

function displayTeamSettings (teamId) {
    switch (teamId) {
        case "public":
            document.getElementById("form_team_settings").style.display = "None";
            break;
        default:
            document.getElementById("form_team_settings").style.display = "block";
    }
}


function displayTileServer (tileServerName, which) {
    switch (tileServerName) {
        case "custom":
            document.getElementById("tileServer"+which+"UrlField").style.display = "block";
            document.getElementById("tileServer"+which+"LayerNameField").style.display = "block";
            break;
        case "sinergise":
            document.getElementById("tileServer"+which+"UrlField").style.display = "None";
            document.getElementById("tileServer"+which+"LayerNameField").style.display = "block";
            break;
        default:
            document.getElementById("tileServer"+which+"UrlField").style.display = "None";
            document.getElementById("tileServer"+which+"LayerNameField").style.display = "None";
    }
    addTileServerCredits(tileServerName, which)
}

function clear_fields() {
    console.log('clear fields.')
    document.getElementById('projectNumber').value = 1
    document.getElementById('inputAoi').value = null
    $(".geometryInfo").each(()=>{$(this).text('')})
    document.getElementById('geometryContent').innerHTML = ''
    aoiLayer.clearLayers()
    displayProjectTypeForm("build_area")
  }

function displaySuccessMessage() {
  //document.getElementById("import-formular").style.display = "None";
  alert('Your project has been uploaded. It can take up to one hour for the project to appear in the dashboard.')
}

function displayImportForm() {
  document.getElementById("import-formular").style.display = "block";
}

function openFile(event) {
    var input = event.target;
    let maxFilesize, maxFeatures;

    if(input.id=="inputAoi"){
        maxFilesize = 1 * 1024 * 1024
        maxFeatures = 10
    }
    else if (input.id=="inputTaskGeometriesFile"){
        maxFilesize = 10 * 1024 * 1024
        maxFeatures = 5000
    }

    // clear info field
    var info_output = $(input).siblings(".geometryInfo")[0];
    info_output.innerHTML = '';
    info_output.style.display = 'block'

    // clear map layers
    aoiLayer.clearLayers()

    // Check file size before loading
    var filesize = input.files[0].size;
    if (filesize > maxFilesize) {
      var err=`filesize is too big (max ${maxFilesize}MB): ${filesize/(1024*1024)}`
      info_output.innerHTML = '<b>Error reading GeoJSON file</b><br>' + err;
      info_output.style.display = 'block'
    } else {
      info_output.innerHTML += 'File Size is valid <br>';
      info_output.style.display = 'block'

      var reader = new FileReader();
      reader.onload = function(){

          try {
              var text = reader.result;
              var geojsonData = JSON.parse(text)
              // check number of features
              numberOfFeatures = geojsonData['features'].length

              console.log('number of features: ' + numberOfFeatures)
              if (numberOfFeatures > maxFeatures) {
                throw 'too many features: ' + numberOfFeatures
              }
              info_output.innerHTML += 'Number of Features: ' + numberOfFeatures + '<br>';
              info_output.style.display = 'block'

              sumArea = 0
              // check input geometry type
              for (var i =0; i < geojsonData.features.length; i++) {
                feature = geojsonData.features[i]
                type = turf.getType(feature)
                console.log('geometry type: ' + type)

                if (type !== 'Polygon' & type !== 'MultiPolygon') {
                    throw 'GeoJson contains one or more wrong geometry type(s): ' + type
                }
                if (input.id=="inputAoi"){
                    info_output.innerHTML += 'Feature Type: ' + type + '<br>';
                    info_output.style.display = 'block'
                }
                sumArea += turf.area(feature)/1000000 // area in square kilometers
               }

              // check project size, based on zoom level
              var zoomLevel = parseInt(document.getElementById('zoomLevel').value);
              // 20,480 sqkm for zoom 17
              //  5,120 sqkm for zooom 18
              //  1,280 sqkm for zoom 19
              maxArea = 5 * (4 ** (23 - zoomLevel))
              console.log('project size: ' + sumArea + ' sqkm')

              if (sumArea > maxArea) {
                throw 'project is to large: ' + sumArea + ' sqkm; ' + 'max allowed size for this zoom level: ' + maxArea + ' sqkm'
              }

              info_output.innerHTML += 'Project Size: ' + sumArea + ' sqkm<br>';
              info_output.style.display = 'block'

              // add feature to map
              aoiLayer.addData(geojsonData);
              ProjectAoiMap.fitBounds(aoiLayer.getBounds());
              console.log('added input geojson feature')

              // add text to html object
              info_output.innerHTML += 'Project seems to be valid :)';
              info_output.style.display = 'block'

              // set project aoi geometry
              projectAoiGeometry = text
            }
            catch(err) {
              info_output.innerHTML = '<b>Error reading GeoJSON file</b><br>' + err;
              info_output.style.display = 'block'
            }
        };
    reader.readAsText(input.files[0]);
    }
  };

function openImageFile(event) {
    var input = event.target;
    element_id = event.target.id + 'File'

    var reader = new FileReader();
    reader.onload = function(){
      try {
        var dataURL = reader.result;
        var output = document.getElementById(element_id);
        output.src = dataURL;
      }
      catch(err) {
          element_id = event.target.id + 'Text'
          var output = document.getElementById(element_id);
          output.innerHTML = '<b>Error reading Image file</b><br>' + err;
        }
    };
    reader.readAsDataURL(input.files[0]);
  };

function closeModal() {
    var modal = document.getElementById("uploadModal");
    modal.style.display = "none";
    var modalSuccess = document.getElementById("modalSuccess");
    modalSuccess.style.display = "none";
}


function show_input(select){
    let link_div = $("#inputTaskGeometries_Link");
    let file_div = $("#inputTaskGeometries_File");
    let id_div = $("#inputTaskGeometries_ProjectId");

    switch(select.value){
        case "link":
            link_div.css("display", "block");
            file_div.css("display", "none");
            id_div.css("display", "none");
            break;
        case "file":
            link_div.css("display", "none");
            file_div.css("display", "block");
            id_div.css("display", "none");
            break;
        case "id":
            link_div.css("display", "none");
            file_div.css("display", "none");
            id_div.css("display", "block");
            break;
    }
}