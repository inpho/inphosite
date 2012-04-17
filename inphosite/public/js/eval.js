var inpho = inpho || {};
inpho.eval = inpho.eval || {};

inpho.eval.submit = function(elt) {
    var formElm = elt + '-eval';
    // antecedent term
    var id   = $(formElm + " [name='ante_id']").val();
    // consequent term
    var id2  = $(formElm + " [name='cons_id']").val();
    // submitted generality value
    var generality  = $(formElm + " #generalitySelect").val();
    // submitted relatedness value
    var relatedness = $(formElm + " #relatednessSelect").val();
   
    // url to post generality value
    var url_gen = '/idea/' + id + '/generality/' + id2;
            var url_rel = '/idea/' + id + '/relatedness/' + id2;
    // submit generality value
    $.post(url_gen,
           { degree : generality },
           function(data){
               // submit relatedness after generality
               $.post(url_rel,
                      { degree : relatedness },
                      function(data){
                          // display thanks form
                          if (generality != '-1' && relatedness != '-1') {
                               inpho.eval.get_thanks_form(elt);
                          }
                      } 
               );
           } );

    // url to post relatedness value
};

inpho.eval.reset = function(elt) {
    var formElm = elt + '-eval';
    // antecedent term
    var id   = $(formElm + " [name='ante_id']").val();
    // consequent term
    var id2  = $(formElm + " [name='cons_id']").val();
    // submitted generality value
    $(formElm + " #generalitySelect").val('-1');
    // submitted relatedness value
    $(formElm + " #relatednessSelect").val('-1');
    
    inpho.eval.submit(elt);
};

inpho.eval.get_edit_form = function(elt) {
    // antecedent term
    var id   = $(elt + " [name='ante_id']").val();
    // consequent term
    var id2  = $(elt + " [name='cons_id']").val();

    var url = "/idea/" + id + "/evaluation/" + id2 + "?edit=1"
    var form = $.get(url, function(data){ 
        $(elt + '-eval').alert('close');
        $(elt).prepend(data);
    });
};

inpho.eval.get_thanks_form = function(elt) {
    // antecedent term
    var id   = $(elt + " [name='ante_id']").val();
    // consequent term
    var id2  = $(elt + " [name='cons_id']").val();
    // submitted generality value
    var generality  = $(elt + " #generalitySelect").val();
    // submitted relatedness value
    var relatedness = $(elt + " #relatednessSelect").val();

    var url = "/idea/" + id + "/evaluation/" + id2 + "?edit=&relatedness=" + relatedness + "&generality=" + generality;
    var form = $.get(url, function(data){ 
        $(elt + '-eval').alert('close');
        $(elt).prepend(data);
    });
};

inpho.eval.validate = function(elt) {
    if ($(elt + " #relatednessSelect").val() == '0' ||
        $(elt + " #relatednessSelect").val() == '-1') {
        $(elt + " #generalitySelect").val('-1');
        $(elt + " #generalitySelect").attr('disabled', 'disabled');
    } else {
        $(elt + " #generalitySelect").attr('disabled', false);
    }
}
