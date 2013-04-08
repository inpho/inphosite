var inpho = inpho || {};
inpho.eval = inpho.eval || {};

// default to alert mode. Individual pages can disable this.
inpho.eval.alert = true;

// *******************
// User Authentication
// *******************
inpho.eval.basicAuth = null;
inpho.eval.cookieAuth = null;

inpho.eval.makeBaseAuth = function(user, pass) {
  var tok = user + ':' + pass;
  var hash = Base64.encode(tok);
  return "Basic " + hash;
}

// ************************
// Cross-domain Evaluations
// ************************
inpho.eval.loadEvalsListFromJSONDataWithFade = function(json, fade) {
  var anteID = json.ID;
  var relatedTerms = json.related;
  var length = (relatedTerms.length > 10) ? 10 : relatedTerms.length;
  var loadingSpinner = $('#loading', '#container');

  $(loadingSpinner).fadeOut('slow', function() {
    $('#container').remove('#loading');
  
    var evals = [];
    for(var i = 0; i < length; i++) {
      var consID = relatedTerms[i];
      $('#evalList').append('<li class="evalItem-eval hide"><div id=i' + consID + '-eval></div></li>');
      inpho.eval.getEvalForm(anteID, consID);

      evals.push($('#i' + consID + '-eval').parent());
    }

    if(fade === 'slow')
      inpho.eval.fadeInEvalsList(0, evals);
    else if(fade === 'fast')
      inpho.eval.showAllEvals();
  });
}

inpho.eval.fadeInEvalsList = function(n, evalList) {
  if(n >= evalList.length) {
    return;
  }
  else {
    setTimeout(function() {
      evalList[n].fadeIn('slow', function() {
        inpho.eval.fadeInEvalsList(n+1, evalList);
      });
    }, 0);
  }
}

inpho.eval.showAllEvals = function() {
  $('.evalItem-eval').fadeIn('slow', null);
}

inpho.eval.displayErrorAlertInDivWithMessage = function(divID, msg) {
  $(divID).append('<div class="alert alert-error alert-block">' +
                  '<h3>Error!</h3>' +
                  '<p>' + msg + '</p><br/><br/>' +
                  '</div>');
}

inpho.eval.displayPromptForArticle = function(divID, label, sepdir) {
  var url = "http://plato.stanford.edu/entries/" + sepdir;
  $(divID).html('Please evaluate the following relevant terms for the article ' +
                '<em><a href="' + url + '" target="_blank">' + label + '</a></em>.');
  $(divID).fadeIn('slow', null);
}

// ****************
// Evaluation Forms
// ****************
inpho.eval.getEvalForm = function(anteID, consID) {
  var url = "/idea/" + anteID + "/evaluation/" + consID + "?edit=1";
  if (!inpho.eval.alert) url += '&alert=';

  $.ajax({
      type: "GET",
      url: inpho.util.url(url),
      success: function(data) {
        var p = $('#i' + consID + '-eval').parent();
        if (inpho.eval.alert) $('#i' + consID + '-eval').alert('close');
        else $('#i' + consID + '-eval').remove();
        $(p).prepend(data);
      },
      beforeSend: function(req) {
        req.setRequestHeader('Authorization',inpho.eval.basicAuth);
      },
      complete: function() {
        console.log("getEvalForm complete");
      }
  });
}

inpho.eval.getThanksForm = function(form) {
  var anteID = $(form).attr('data-anteID');
  var consID = $(form).attr('data-consID');

  var relDiv = $('.relatednessSelect', form);
  var genDiv = $('.generalitySelect', form);

  var relVal = inpho.eval.getValueFromButtonGroupDiv(relDiv);
  var genVal = inpho.eval.getValueFromButtonGroupDiv(genDiv);

  var url = "/idea/" + anteID + "/evaluation/" + consID + "?edit=&relatedness=" + relVal + "&generality=" + genVal;
  if (!inpho.eval.alert) url += '&alert=';

  $.ajax({
      type: "GET",
      url: inpho.util.url(url),
      success: function(data){
        var p = $('#i' + consID + '-eval').parent();
        if (inpho.eval.alert) $('#i' + consID + '-eval').alert('close');
        else $('#i' + consID + '-eval').remove();
        $(p).prepend(data);
      },
      beforeSend: function(req) {
        req.setRequestHeader('Authorization',inpho.eval.basicAuth);
      },
      complete: function() {
        console.log("getThanksForm complete");
      }
  });
};

// *********************
// Evaluation Submission
// *********************
inpho.eval.submitEval = function(ante_id, cons_id, rel, gen, callback) {
    console.log("submitEval: " + ante_id + "," + cons_id + "," + rel + "," + gen);

    // urls to post generality and relatedness values
    var url_rel = '/idea/' + ante_id + '/relatedness/' + cons_id;
    var url_gen = '/idea/' + ante_id + '/generality/' + cons_id;

    $.ajax({
      type: "POST",
      url: inpho.util.url(url_rel),
      data: { degree : rel, cookieAuth : inpho.eval.cookieAuth },
      success: function(data) {
    	  $.ajax({
    	      type: "POST",
    	      url: inpho.util.url(url_gen),
    	      data: { degree : gen, cookieAuth : inpho.eval.cookieAuth },
    	      success: callback,
    	      beforeSend: function(req) {
    		      req.setRequestHeader('Authorization',inpho.eval.basicAuth);
    	      },
    	      complete: function() {
    		      console.log("auth submit gen complete");
    	      }
    	  });
      },
      beforeSend: function(req) {
        req.setRequestHeader('Authorization', inpho.eval.basicAuth);
      },
      complete: function() {
        console.log("auth submit rel complete");
      }
    });
}

inpho.eval.resetEval = function(ante_id, cons_id) {
    inpho.eval.submitEval(ante_id, cons_id, -1, -1);
};

inpho.eval.deleteEval = function(form) {
    var anteID = $(form).attr('data-anteID');
    var consID = $(form).attr('data-consID');
    
    inpho.eval.resetEval(anteID, consID);

    if (inpho.eval.alert) $('#i' + consID + '-eval').alert('close');
    else $('#i' + consID + '-eval').remove();
}

inpho.eval.cancelEval = function(form) {
    var anteID = $(form).attr('data-anteID');
    var consID = $(form).attr('data-consID');

    var url = "/idea/" + anteID + "/evaluation/" + consID + "?edit=";
    if (!inpho.eval.alert) url += '&alert=';

    $.ajax({
      type: "GET",
      url: inpho.util.url(url),
      success: function(data) {
        var p = $('#i' + consID + '-eval').parent();
        if (inpho.eval.alert) $('#i' + consID + '-eval').alert('close');
        else $('#i' + consID + '-eval').remove();
        $(p).prepend(data);
      },
      beforeSend: function(req) {
        req.setRequestHeader('Authorization',inpho.eval.basicAuth);
      },
      complete: function() {
        console.log("cancelEval complete");
      }
  });
}

// *************
// Evaluation UI
//**************
inpho.eval.parseAndSubmit = function(form) {
    inpho.eval.animateSpinner(form);

    var anteID = $(form).attr('data-anteID');
    var consID = $(form).attr('data-consID');

    var relDiv = $('.relatednessSelect', form);
    var genDiv = $('.generalitySelect', form);

    var relVal = inpho.eval.getValueFromButtonGroupDiv(relDiv);
    var genVal = inpho.eval.getValueFromButtonGroupDiv(genDiv);

    inpho.eval.submitEval(anteID, consID, relVal, genVal,
      function () { 
        inpho.eval.getThanksForm(form) 
      });
}

inpho.eval.animateSpinner = function(form) {
    $(form).fadeOut('fast', function() {
      var spinnerDiv = $('.spinner', $(form).parent());
      $(spinnerDiv).fadeIn('fast', null);
    });
}

inpho.eval.didSelectRelatedness = function(button) {
    var form = button.form;
    var generalityDiv = $('.generalitySelect', form);
    var submitDiv = $('.submitBtns', form);

    // update UI
    inpho.eval.resetButtonGroup(generalityDiv);
    
    if($(button).val() == 0) { // not related, show submit
        $(generalityDiv).fadeOut('slow', null);
        $(submitDiv).fadeIn('fast', null);
    }
    else { // are related, show generality
        $(submitDiv).fadeOut('fast', null);
        $(generalityDiv).fadeIn('slow', null);
    }
}

inpho.eval.didSelectGenerality = function(button) {
  // update UI, show submit
  var form = button.form;
  var submitDiv = $('.submitBtns', form);
  $(submitDiv).fadeIn('fast', null);
}

inpho.eval.getValueFromButtonGroupDiv = function(btnGroupDiv) {
    for(var i = 0; i < $(btnGroupDiv).children().length; i++) {
        var btn = $($(btnGroupDiv).children()[i]);
        if(btn.hasClass('active')) {
            return $(btn).val();
        }
    }
    return -1;
}   

inpho.eval.getHTMLFromButtonGroupDiv = function(btnGroupDiv) {
    for(var i = 0; i < $(btnGroupDiv).children().length; i++) {
        var btn = $($(btnGroupDiv).children()[i]);
        if(btn.hasClass('active')) {
            return $(btn).html();
        }
    }
    return null;
}

inpho.eval.resetButtonGroup = function(btnGroupDiv) {
    for(var i = 0; i < $(btnGroupDiv).children().length; i++) { 
        $($(btnGroupDiv).children()[i]).removeClass('active');
    }
}