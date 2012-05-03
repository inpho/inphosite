// initialize namespaces
inpho = inpho || {};
inpho.admin = inpho.admin || {};

inpho.admin.process_text = function(e, attr, url) {
    if ((e.keyCode == 13) || (e.keyCode == 9)) { // Enter and Tab support
        e.preventDefault();
        if ($('#'+attr).val() != '')
            inpho.admin.submit_field(attr, url);
        return false;
    } else if (e.keyCode == 27) { // Escape 
        return inpho.admin.reset_field(attr, url);
    } else {
        var status_icon = $('.input-status', $('#'+attr).parent());
        status_icon.removeClass('icon-ok');
        status_icon.removeClass('icon-warning-sign');
        status_icon.removeClass('icon-loading');
        status_icon.parents('.control-group').removeClass('success');
        status_icon.parents('.control-group').removeClass('error');
        status_icon.addClass('icon-share-alt');
    }
}

inpho.admin.submit_field = function(attr, url) {
  var status_icon = $('.input-status', $('#' + attr).parent());
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
            if (xhr.status < 400) {
              status_icon.removeClass('icon-loading');
              status_icon.addClass('icon-ok');
              status_icon.parents('.control-group').addClass('success');
              if (attr == "searchpatterns" || attr == "abbrs" || attr == "queries") {
                  var val = value;
                  val = val.replace("<", "&lt;")
                  val = val.replace(">", "&gt;")
                  var new_entry = '<label><i class="icon-remove" onclick="return inpho.admin.remove(this.parentNode, \'' + attr + '\', \'' + url + '\')"></i>' + val + '</label>';
                  $('#'+attr).before(new_entry);
                  $('#'+attr).val('');
              }
            } else {
              status_icon.removeClass('icon-loading');
              status_icon.parents('.control-group').addClass('error');
              status_icon.addClass('icon-warning-sign');
            }
        }
      }
  }
  xhr.open('PUT', url, true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  $('#'+attr+' .input-status').removeClass('icon-*');
  
  status_icon.removeClass('icon-share-alt');
  status_icon.addClass('icon-loading');
  if (attr == "searchpatterns" || attr == "abbrs" || attr == "queries")
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
inpho.admin.reset_field = function(attr, url) {
  if (response == 200)
    var attr_value = document.getElementById(attr).value;
  // PUT was not successful:
  else
    var attr_value = document.getElementById(attr).value;
  
  if (attr == "searchpatterns" || attr == "abbrs" || attr == "queries")
    $('#'+attr).val('');

  //document.getElementById(attr_edit).style.visibility = 'visible';
  return true;
}
