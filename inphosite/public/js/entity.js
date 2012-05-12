var inpho = inpho || {};
inpho.entity = inpho.entity || {};

inpho.entity.showMore = function (attr, id, n, start) {
    // build url to grab attribute
    var url = $('#' + attr).attr('data-source');
    url += "?limit=" + n + "&start=" + start;

    // get attribute data
    $.getJSON(url, function (data) { 
        // append each item to the list
        for (i in data.responseData.results) {
            var idea = data.responseData.results[i];
            var item = '<li><a onClick="inpho.tabnav.appendTab(\'tabnav\', \'i'+ idea.ID +'\', \''+ idea.label + '\', \'/idea/' + idea.ID + '/panel/' + id + '\')" href="#i'+ idea.ID + '" data-toggle="tab">' + idea.label + '</a></li>';
            $('#' + attr + ' ol .more').before(item);
        }

        // if there are still more entries, correct the "show more" button,
        // otherwise remove the "show more" button.
        if (data.responseData.total > (start + n)) {
            var onClick =  "inpho.entity.showMore('"+attr+"', " + id + ", " + n + ", " + (start + n) + ")";
            $('#' + attr + ' ol .more a').attr('onClick', onClick);
            $('#' + attr + ' ol .more a').text('Show more… (' + (data.responseData.total - start - n) + ')');
        } else {
            $('#' + attr + ' ol .more').remove();
        }
    });
}
