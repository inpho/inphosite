var inpho = inpho || {};
inpho.eval = inpho.eval || {};

// default to alert mode. Individual pages can disable this.
inpho.eval.alert = true;

// *******************
// User Authentication
// *******************
inpho.eval.userAuth = null;

inpho.eval.makeBaseAuth = function(user, pass) {
  var tok = user + ':' + pass;
  var hash = Base64.encode(tok);
  return "Basic " + hash;
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
        req.setRequestHeader('Authorization',inpho.eval.userAuth);
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
        req.setRequestHeader('Authorization',inpho.eval.userAuth);
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
      data: { degree : rel },
      success: function(data) {
    	  $.ajax({
    	      type: "POST",
    	      url: inpho.util.url(url_gen),
    	      data: { degree : gen },
    	      success: callback,
    	      beforeSend: function(req) {
    		      req.setRequestHeader('Authorization',inpho.eval.userAuth);
    	      },
    	      complete: function() {
    		      console.log("auth submit gen complete");
    	      }
    	  });
      },
      beforeSend: function(req) {
        req.setRequestHeader('Authorization', inpho.eval.userAuth);
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
        req.setRequestHeader('Authorization',inpho.eval.userAuth);
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