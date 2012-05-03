// initialize namespaces
inpho = inpho || {};
inpho.admin = inpho.admin || {};

inpho.admin.process_text = function(e, attr, url) {
    if ((e.keyCode == 13) || (e.keyCode == 9)) { // Enter and Tab support
        e.preventDefault();
        if ($('#'+attr).val() != '')
            inpho.admin.submit_field(attr, url);
        return false;
    }
    if (e.keyCode == 27) { // Escape 
        return inpho.admin.reset_field(attr, url, 400);
    }
}

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
            if (attr == "searchpatterns" || attr == "abbrs" || attr == "queries") {
                var val = value;
                val = val.replace("<", "&lt;")
                val = val.replace(">", "&gt;")
                var new_entry = '<label class="input-large">' + val +
                    '<i class="pull-right icon-remove" onclick="return inpho.admin.remove(this.parentNode, \'' + attr + '\', \'' + url + '\')"></i></label>';
                $('#searchpatterns').before(new_entry);
                $('#searchpatterns').val('');
            }
        }
      }
  }
  xhr.open('PUT', url, true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  if (attr == "searchpatterns")
    xhr.send("pattern=" + value);
  else
    xhr.send(attr + "=" + value);
}

inpho.admin.remove = function(elt, attr, url) {   
  var value = "?pattern=" + encodeURIComponent($(elt).text());
  url = url + value
  var xhr = new XMLHttpRequest();
      xhr.onreadystatechange = function () {
        if (xhr.readyState == 4) {
            $(elt).remove();
        }
      }
  xhr.open('DELETE', url, true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send(); 
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
