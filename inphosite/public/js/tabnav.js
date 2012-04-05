var inpho = inpho || {};
inpho.tabnav = inpho.tabnav || {};

inpho.tabnav.removeTab = function(tab, content) {
    // remove tab
    $(tab).remove();

    // check if active, move to home tab if so
    if ($(content).hasClass('active')) {
        $('#home-tab').addClass('active');
        $('#home').addClass('active');
    }
    // remove tab content
    $(content).remove();
}

inpho.tabnav.appendTab = function(tabNav, id, title, url) {
    // if tab does not exist, append new tab
    if ($('#'+id).length == 0) {
        // append new nav header
        var remove = '<i class="icon-remove remove" onClick="inpho.tabnav.removeTab(\'#'+id+'-tab\', \'#'+id+'\')"></i>';
        $('#'+tabNav).append('<li id="'+id+'-tab"><a href="#'+id+'" data-toggle="tab">'+title+' '+remove+'</a></li>');    
    
        // append temporary loading pane
        var tempPane = '<div class="tab-pane" id="'+id+'">Loading content... <img src="/img/loading.gif" /></div>'
        $('#'+tabNav+'-content').append(tempPane);
    
        // append new tab content
        // make an AJAX call to grab the panel
        $.get(url, function(data){
            $('#'+id).html(data);
        });
    }

    inpho.tabnav.switchTab(tabNav, id);
}

inpho.tabnav.switchTab = function(tabNav, id) {
    // flip to new tab, regardless of existence
    $('#'+tabNav+' .active').removeClass('active');
    $('#'+id+'-tab').addClass('active');
    $('#'+tabNav+'-content .active').removeClass('active');
    $('#'+id).addClass('active');
}

