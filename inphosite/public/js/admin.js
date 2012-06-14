// initialize namespaces
inpho = inpho || {};
inpho.admin = inpho.admin || {};


// *** TEXT FIELD PROCESSING *** //
// For our text fields, we use several events to change a status icon
// corresponding to each control:
// * keydown captures enter and tab to submit the field without submitting the
//   default html form.
// * keyup caputres enter again and fires a change event for all non-tab chars
// * change ensures that the status reflects the current state of the database.
//   if a newly input character causes this to go out of sync, the status icon
//   changes to a submit icon. If later changes cause it to go back in sync, the
//   status icon changes back to the checkmark.

// inpho.admin.process_keydown
// For use with the onkeydown handler to intercept enter and tab keypresses
// and trigger form submission.
inpho.admin.process_keydown = function(e) {
  var status_icon = $('.input-status', $(this).parent());
  if ((e.keyCode == 13) || (e.keyCode == 9)) { // Enter and Tab support
    // submit the form
    if (status_icon.hasClass('icon-share-alt') && 
         !$(this).hasClass('admin-date') )
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
  } else if (e.keycode != 9) {
    $(this).change();
  }
}
// bind keyup to .admin-text on document.ready()
$(function() { $('.admin-text').bind('keyup', inpho.admin.process_keyup) });

inpho.admin.process_change = function(e) {
  /*alert('during change: ' + $(this).val()
    + '\ndefault: ' + this.defaultValue);*/

  var status_icon = $('.input-status', $(this).parent());
  if ($(this).val() != this.defaultValue) {
    status_icon.removeClass('icon-ok');
    status_icon.removeClass('icon-loading');
    status_icon.removeClass('icon-warning-sign');
    $(this).parents('.control-group').removeClass('success');
    $(this).parents('.control-group').removeClass('error');
    status_icon.addClass('icon-share-alt');
  } else {
    status_icon.removeClass('icon-loading');
    status_icon.removeClass('icon-warning-sign');
    status_icon.removeClass('icon-share-alt');
    status_icon.addClass('icon-ok');
  }
}
$(function() { $('.admin-text').bind('change', inpho.admin.process_change) });


inpho.admin.submit_field = function(attr, url) {
  var status_icon = $('.input-status', $('#' + attr).parent());
  var value = document.getElementById(attr).value;
  if (attr == "URL") {
    if (value && (value.substring(0, 4) != "http")
        && (value.substring(0, 4).toLowerCase() != "none"))
      value = "http://" + value;
    value = decodeURIComponent(value);
    value = encodeURIComponent(value);
  }
  else if (attr == "active" || attr == "openAccess" || attr == "student") {
    if (document.getElementById(attr).checked)
      value = "1";
    else
      value = "0";
  }

  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (xhr.readyState == 4) {
      if (xhr.status < 400) {
        status_icon.removeClass('icon-share-alt');
        status_icon.removeClass('icon-loading');
        status_icon.addClass('icon-ok');
        $('#'+attr).parents('.control-group').addClass('success');
        if (attr == "searchpatterns" || attr == "abbrs" || attr == "queries") {
          var val = value;
          val = val.replace("<", "&lt;")
          val = val.replace(">", "&gt;")
          var new_entry = '<label><i class="icon-remove" onclick="return inpho.admin.remove(this.parentNode, \'' + attr + '\', \'' + url + '\')" data-url="' + url + '"></i> ' + val + ' </label>';
          $('#'+attr).before(new_entry);
          $('#'+attr).val('');
        } else {
          if (attr == "URL") value = decodeURIComponent(value);
          // change the default value to the newly submitted value
          $('#'+attr)[0].defaultValue = value;
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
  
  $('#'+attr).parents('.control-group').removeClass('error');
  $('#'+attr).parents('.control-group').removeClass('success');
  status_icon.removeClass('icon-warning-sign');
  status_icon.removeClass('icon-share-alt');
  status_icon.removeClass('icon-ok');
  status_icon.addClass('icon-loading');
  if (attr == "searchpatterns" || attr == "abbrs" || attr == "queries")
    xhr.send("pattern=" + value);
  else
    xhr.send(attr + "=" + value);
}

inpho.admin.submit_form = function(form, url) {
  var form_elt = $('#'+form);
  form_elt = $('.control-group', form_elt);
  var status_icon = $('.input-status', form_elt);
  form_elt.removeClass('error');
  form_elt.removeClass('warning');
  form_elt.removeClass('success');
  status_icon.removeClass('icon-warning-sign');
  status_icon.removeClass('icon-share-alt');
  status_icon.addClass('icon-loading');
  $('.help-inline', form_elt).remove();

  var data = $("#"+form).serialize();
  $.post(url, data)
   .success(function() {
        status_icon.removeClass('icon-share-alt');
        status_icon.removeClass('icon-loading');
        status_icon.addClass('icon-ok');
      
        // check if the date is already in the list of dates
        var identical = $.grep($('.control-date-label', form_elt), function (elt,n) {
          return $(elt).attr('data-value') == inpho.admin.build_date_string(form);
        });

        // behave accordingly
        if (identical.length == 0) {
          form_elt.addClass('success');

          var new_entry = '<label class="control-date-label" data-value="' + inpho.admin.build_date_string(form) + '"><i class="icon-remove" onclick="return inpho.admin.remove_date(this.parentNode, \'' + url + '\')" data-url="' + url + '"></i> ' + inpho.admin.build_date_pretty_string(form) + ' </label>';
          $('.input-append', form_elt).before(new_entry);
        } else {
          var warning = '<span class="help-inline">Date already submitted.</span>';
          $('.input-append', form_elt).after(warning);
        }

        // reset fields
        $('select', form_elt).val('0');
        $('input', form_elt).val('');
        
        // change status icon
        status_icon.removeClass('icon-ok');
        status_icon.addClass('icon-share-alt');
    }
  )
  .error(function(jqXHR, textStatus, errorThrown) {
        status_icon.removeClass('icon-share-alt');
        status_icon.removeClass('icon-loading');
        status_icon.addClass('icon-warning-sign');

        if (jqXHR.status == 500) {
          form_elt.addClass('error');
          var warning = '<span class="help-inline">' + errorThrown + '</span>';
          $('.input-append', form_elt).after(warning);
        } else {
          form_elt.addClass('warning');
          var response = $.parseJSON(jqXHR.responseText);
          var warning = '<span class="help-inline">' + response.responseDetails + '</span>';
          $('.input-append', form_elt).after(warning);
        }
    });
}

String.prototype.startsWith = function(str) {return (this.match("^"+str)==str)}

inpho.admin.change_date = function(form) {
  var form_elt = $('#'+form);
  form_elt = $('.control-group', form_elt);
  var status_icon = $('.input-status', form_elt);
  form_elt.removeClass('error');
  form_elt.removeClass('warning');
  form_elt.removeClass('success');
  status_icon.removeClass('icon-warning-sign');
  status_icon.removeClass('icon-loading');
  status_icon.addClass('icon-share-alt');
  $('.help-inline', form_elt).remove();
 
  var year = $("[name='year']", form_elt).val();
  if (year.startsWith('-')) {
    // remove slash and set era
    $("[name='year']", form_elt).val(year.substr(1));
    $("[name='era']", form_elt).val('bce');
    }

  }

inpho.admin.build_date_string = function(form) {
  var f = $('#'+form);
  var day = $('[name=day]', f).val();
  if (day.length == 1) day = '0' + day;
  var month = $('[name=month]', f).val(); 
  if (month.length == 1) month = '0' + month;
  
  var era = $('[name=era]', f).val();
  var year = $('[name=year]', f).val(); 
  if (era != 'bce') year = (Number(year)-1).toString();
  if (year.length != 4) year = '0' + year;
  if (year.length != 4) year = '0' + year;
  if (year.length != 4) year = '0' + year;
  if (year.length != 4) year = '0' + year;
  
  var str = year + month + day;

  if (era ==  'bce') str = '-' + str;

  return str;
}

var months = {
  '1' : 'January',
  '2' : 'February',
  '3' : 'March',
  '4' : 'April',
  '5' : 'May',
  '6' : 'June',
  '7' : 'July',
  '8' : 'August',
  '9' : 'September',
  '10' : 'October',
  '11' : 'November',
  '12' : 'December'
};

inpho.admin.build_date_pretty_string = function(form) {
  var f = $('#'+form);
  var str = '';
  var day = $('[name=day]', f).val();
  var month = $('[name=month]', f).val();
  var era = $('[name=era]', f).val();
  var year = $('[name=year]', f).val(); 

  if (month != '' && month != '0') str += months[month] + " ";
  if (day != '' && day != '0') str += day + ", ";
  str += year;
  if (era == 'bce') str += " B.C.E."

  return str;
}

inpho.admin.build_date_obj = function(form) {
  var f = $('#'+form);
  var day = $('[name=day]', f).val();
  var month = $('[name=month]', f).val(); 
  var year = $('[name=year]', f).val(); 
  var era = $('[name=era]', f).val();

  if (era ==  'bce') year = year * -1;

  var d = new Date(year, month, day);
  return d;
}

inpho.admin.remove = function(elt, attr, url) {
  var value = "?pattern=" + encodeURIComponent($(elt).text());
  url = url + value
  $.ajax({ type: 'DELETE', url: url,
           success: function() { $(elt).remove()} });
}

inpho.admin.remove_date = function(elt, url) {
  var value = "?string=" + $(elt).attr('data-value');
  url = url + value
  $.ajax({ type: 'DELETE', url: url,
           success: function() { $(elt).remove()} });
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
