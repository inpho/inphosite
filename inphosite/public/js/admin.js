// initialize namespaces
inpho = inpho || {};
inpho.admin = inpho.admin || {};

inpho.admin.process_text = function(e, attr, url) {
    if ((e.keyCode == 13) || (e.keyCode == 9)) // Enter and Tab support
        return inpho.admin.submit_field(attr, url);
    if (e.keyCode == 27) { // Escape 
        return inpho.admin.reset_field(attr, url, 400);
    }
    if (attr == "URL")
        return inpho.admin.toggle_test_url(attr);
}

spid=100;
inpho.admin.submit_field = function(attr, url) {
  var value = document.getElementById(attr).value;
  if (attr == "URL") {
      if (value && (value.substring(0, 4) != "http"))
        value = "http://" + value;
      var value = attr + "=" + encodeURIComponent(value);
  }
  else if (attr == "active" || attr == "openAccess" || attr == "student") {
      if (document.getElementById(attr).checked)
        var value = attr + "=1";  
      else
        var value = attr + "=0";
  }
  
  if (value == "None" || value == "undefined") {
    value = "";
  }
  
  var xhr = new XMLHttpRequest();
  if (attr != "active" && attr != "openAccess" && attr != "student") {
      xhr.onreadystatechange = function () {
        if (xhr.readyState == 4) {
            inpho.admin.reset_field(attr, url, xhr.status);
            if (attr == "searchpattern") {
                spid = spid + 1;
                var attr_text = attr + "_text";
                var new_entry = '<li class="idea" id="searchpattern'+spid+'"><span id="searchpattern'+spid+'_edit" class="sep" onclick="inpho.admin.removesp(\'searchpattern'+spid+'\',\''+url+'\')"><img src="/img/delete.png" width=18 height=18 /></span><span id="searchpattern'+spid+'_field"></span></li>';
                var val = value.split('=')[1]
                val = val.replace("<", "&lt;")
                val = val.replace(">", "&gt;")
                $('#new_searchpattern').before(new_entry);
                $("#searchpattern"+spid+"_field").html(val);
            }
        }
      }
  }
  xhr.open('PUT', url, true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send(attr + "=" + value);
}

// The reset function does the following:
// 1.) The text input box should go back to a static field displaying either 
//     the new property (on success) or the old property (on failure).
// 2.) The edit icon should re-appear.
//
inpho.admin.reset_field = function(attr, url, response) {
  if (response == 200)
    var attr_value = document.getElementById(attr).value;
  // PUT was not successful:
  else
    var attr_value = document.getElementById(attr).value;

  if (attr == "openAccess" && attr_value == 0)
    var attr_value = "Closed";
  else if (attr == "openAccess" && attr_value == 1)
    var attr_value = "Open";
  else if (attr == "active" && attr_value == 0)
    var attr_value = "Inactive";
  else if (attr == "active" && attr_value == 1)
    var attr_value = "Active";
  else if (attr == "student" && attr_value == 0)
    var attr_value = "Student";
  else if (attr == "student" && attr_value == 1)
    var attr_value = "Nonstudent";
  else if (attr == "searchpattern") {
    var attr_value = "Add a New Search Pattern";
  }

  alert("reset field?");
  //document.getElementById(attr_edit).style.visibility = 'visible';
  return true;
}
