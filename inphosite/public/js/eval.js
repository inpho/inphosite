var inpho = inpho || {};
inpho.eval = inpho.eval || {};



// *********************
// Evaluation Submission
// *********************
inpho.eval.submitEval = function(ante_id, cons_id, rel, gen, callback) {
    console.log("submitEval: " + ante_id + "," + cons_id + "," + rel + "," + gen);

    // url to post generality value
    var url_gen = '/idea/' + ante_id + '/generality/' + cons_id;
    var url_rel = '/idea/' + ante_id + '/relatedness/' + cons_id;
    
    // submit generality value
    $.post(url_gen,
           { degree : gen },
           function(data){
             // submit relatedness after generality
             $.post(url_rel,
                    { degree : rel },
                    callback
                  );
           } );
    // url to post relatedness value
}

inpho.eval.resetEval = function(ante_id, cons_id) {
    inpho.eval.submitEval(ante_id, cons_id, -1, -1);
};

inpho.eval.parseAndSubmit = function(form) {
    var anteID = $(form).attr('data-anteID');
    var consID = $(form).attr('data-consID');

    var relDiv = $('.relatednessSelect', form);
    var genDiv = $('.generalitySelect', form);

    var relVal = inpho.eval.getValueFromButtonGroupDiv(relDiv);
    var genVal = inpho.eval.getValueFromButtonGroupDiv(genDiv);

    inpho.eval.submitEval(anteID, consID, relVal, genVal,
      function () { inpho.eval.getThanksForm(form) });
}

inpho.eval.resetWidgetEval = function(elt) {
  var formElm = elt + '-eval';
  // antecedent term
  var id   = $(formElm + " [name='ante_id']").val();
  // consequent term
  var id2  = $(formElm + " [name='cons_id']").val();
  // submitted generality value
  $(formElm + " #generalitySelect").val('-1');
  // submitted relatedness value
  $(formElm + " #relatednessSelect").val('-1');

  $(elt + " #generalitySelect").attr('disabled', 'disabled');
  $(elt + " .and").hide();
  $(elt + " #generalitySelect").hide();

  inpho.eval.submitWidgetEval(elt);
};


// ************************************************
// Full Form (idea-edit.html) Evaluation Submission
// ************************************************
inpho.eval.didSelectRelatedness = function(button) {
    var form = button.form;
    var generalityDiv = $('.generalitySelect', form);
    var submitDiv = $('.submitBtns', form);

    // update UI
    inpho.eval.resetButtonGroup(generalityDiv);
    console.log("here we are");
    if($(button).val() == 0) { // not related, show submit
        $(generalityDiv).fadeOut('slow', null);
        $(submitDiv).fadeIn('fast', null);
        console.log("no generality");
    }
    else { // are related, show generality
        $(submitDiv).fadeOut('fast', null);
        $(generalityDiv).fadeIn('slow', null);
        console.log("WLOG");
    }
}

inpho.eval.didSelectGenerality = function(button) {
  // update UI, show submit
  var form = button.form;
  var submitDiv = $('.submitBtns', form);
  $(submitDiv).fadeIn('fast', null);
}

inpho.eval.didPressSubmit = function(formid) {
  inpho.eval.parseAndSubmit(formid);
  inpho.eval.displayThankYou(formid, true);
}

inpho.eval.displayThankYou = function(formid, shouldUpdateMsg) {
    // update UI hide form, show thanks/edit
    $(document.getElementById(formid)).fadeOut('slow', function() {
        var thanksDiv = document.getElementById("thanksDiv-" + formid);
        
        if(shouldUpdateMsg) {
            var resultSpan = document.getElementById('evalThanksResult-' + formid);
            resultSpan.innerHTML = inpho.eval.getEvalResultMessage(formid);
        }

        $(thanksDiv).fadeIn('slow',null);
    });
}

inpho.eval.getEvalResultMessage = function(formid) {
    var anteTerm = $(document.getElementById("thanksDiv-" + formid)).attr('data-ante');
    var consTerm = $(document.getElementById("thanksDiv-" + formid)).attr('data-cons');
    var relDiv = document.getElementById('relatednessSelect-' + formid);
    var genDiv = document.getElementById('generalitySelect-' + formid);

    var relVal = inpho.eval.getHTMLFromButtonGroupDiv(relDiv);
    var genVal = (inpho.eval.getHTMLFromButtonGroupDiv(genDiv) == null) ? '' : 'and ' + inpho.eval.getHTMLFromButtonGroupDiv(genDiv);

    return '<p class="idea">' + anteTerm + '</p><p> is ' + relVal + ' to ' + genVal + ' </p><p class="idea">' + consTerm + '</p><p>.</p>';
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


// occurs when the edit putton is pushed
inpho.eval.didPressEdit = function(formid) {
    inpho.eval.resetButtonGroup(document.getElementById('generalitySelect-' + formid));
    inpho.eval.resetButtonGroup(document.getElementById('relatednessSelect-' + formid));

    // update UI show form with cancel, hide thanks/edit
    $(document.getElementById('thanksDiv-' + formid)).fadeOut('slow', function() {
        $(document.getElementById('cancelBtn-' + formid)).removeClass('hide');
        $(document.getElementById(formid)).fadeIn('slow', null);
    });
}

inpho.eval.didPressCancel = function(formid) {
    inpho.eval.displayThankYou(formid, false);
}



// ****************************************
// Inline (eval.html) Evaluation Submission
// ****************************************
inpho.eval.getThanksForm = function(form) {
  var anteID = $(form).attr('data-anteID');
  var consID = $(form).attr('data-consID');

  var relDiv = $('.relatednessSelect', form);
  var genDiv = $('.generalitySelect', form);

  var relVal = inpho.eval.getValueFromButtonGroupDiv(relDiv);
  var genVal = inpho.eval.getValueFromButtonGroupDiv(genDiv);

  var url = "/idea/" + anteID + "/evaluation/" + consID + "?edit=&relatedness=" + relVal + "&generality=" + genVal;
  
  $.get(url, function(data){
    var p = $('#i' + consID + '-eval').parent();
    $('#i' + consID + '-eval').alert('close');
    $(p).prepend(data);
  });
};

inpho.eval.didPressEditInline = function(formid, elt) {
  inpho.eval.getEvalForm(formid, elt);
}

inpho.eval.didPressResetInline = function(formid, elt) {
  var anteID = $(document.getElementById(formid)).attr('data-anteID');
  var consID = $(document.getElementById(formid)).attr('data-consID');

  inpho.eval.resetEval(anteID, consID);
  inpho.eval.getEvalFormReset(formid, elt);
}

inpho.eval.getEvalFormReset = function(formid, elt) {
  var anteID = $(document.getElementById(formid)).attr('data-anteID');
  var consID = $(document.getElementById(formid)).attr('data-consID');

  var url = "/idea/" + anteID + "/evaluation/" + consID + "?edit=&relatedness=-1&generality=-1";
  
  $.get(url, function(data){
    $(elt + '-edit').alert('close');
    $(elt).prepend(data);
  });
}

inpho.eval.getEvalForm = function(form) {
  var anteID = $(form).attr('data-anteID');
  var consID = $(form).attr('data-consID');

  var url = "/idea/" + anteID + "/evaluation/" + consID + "?edit=1"
  
  $.get(url, function(data){
    var p = $('#i' + consID + '-eval').parent();
    $('#i' + consID + '-eval').alert('close');
    $(p).prepend(data);
  });
}

inpho.eval.didPressCancelInline = function(elt) {
  $(elt + '-eval').alert('close');
}
