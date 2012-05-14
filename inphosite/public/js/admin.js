// initialize namespaces
inpho = inpho || {};
inpho.admin = inpho.admin || {};

// inpho.admin.process_keydown
// For use with the onkeydown handler to intercept enter and tab keypresses
// and trigger form submission.
inpho.admin.process_keydown = function(e) {
    var status_icon = $('.input-status', $(this).parent());
    if ((e.keyCode == 13) || (e.keyCode == 9)) { // Enter and Tab support
        // submit the form 
        if (status_icon.hasClass('icon-share-alt'))
            inpho.admin.submit_field(this.id, $(this).attr('data-url'));

        // do not use the browser-submit if enter is pressed
        if (e.keyCode == 13) {
            e.preventDefault();
            return false;
        }
    } 
}
// bind keydown to .admin-text on document.ready()
$(function() { $('.admin-text').bind('keydown', inpho.admin.process_keydown) });

// inpho.admin.process_keyup
// For use with the onkeyup handler to intercept enter and tab keypresses and to
// change the status icons
inpho.admin.process_keyup = function(e) {
    if (e.keyCode == 13) {
        // do not do the default form submission
        e.preventDefault();
        return false;
    } else if (e.keyCode == 27) { // Escape 
        return inpho.admin.reset_field(attr, url);
    } else if (e.keyCode != 9) {
        // change the status_icon for all keystrokes, other than tab
        var status_icon = $('.input-status', $(this).parent());
        status_icon.removeClass('icon-ok');
        status_icon.removeClass('icon-warning-sign');
        status_icon.removeClass('icon-loading');
        $(this).parents('.control-group').removeClass('success');
        $(this).parents('.control-group').removeClass('error');
        status_icon.addClass('icon-share-alt');
    }
}
// bind keyup to .admin-text on document.ready()
$(function() { $('.admin-text').bind('keydown', inpho.admin.process_keyup) });


inpho.admin.submit_field = function(attr, url) {
  var status_icon = $('.input-status', $('#' + attr).parent());
  var value = document.getElementById(attr).value;
  if (attr == "URL") {
      if (value 
          && (value.substring(0, 4) != "http")
          && (value.substring(0, 4).toLowerCase() != "none"))
        value = "http://" + value;
      var value = encodeURIComponent(value);
  }
  else if (attr == "active" || attr == "openAccess" || attr == "student") {
      if (document.getElementById(attr).checked)
        value = "1";  
      else
        value = "0";
  }
  
  if (value == "None" || value == "undefined") {
    value = "";
  }
  
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (xhr.readyState == 4) {
        if (xhr.status < 400) {
          status_icon.removeClass('icon-loading');
          status_icon.addClass('icon-ok');
          $('#'+attr).parents('.control-group').addClass('success');
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
          $('#'+attr).parents('.control-group').addClass('error');
          status_icon.addClass('icon-warning-sign');
        }
    }
  }
  xhr.open('PUT', url, true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  $('#'+attr+' .input-status').removeClass('icon-*');
  $('#'+attr).parents('.control-group').removeClass('error');
  $('#'+attr).parents('.control-group').removeClass('success');
  
  status_icon.removeClass('icon-warning-sign');
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
