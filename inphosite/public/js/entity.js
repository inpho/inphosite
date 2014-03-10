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
      var item = '<li>'
        + ' <a onClick="inpho.tabnav.appendTab(\'tabnav\', \'i'+ idea.ID +'\', \''+ idea.label + '\', \'/entity/' + idea.ID + '/panel/' + id + '\')" href="#i'+ idea.ID + '" data-toggle="tab" class="tablink"><i class="icon-search" data-toggle="tooltip" title="Search for '+ idea.label + ' and ' + $("#label").text() + ' on SEP and Noesis"></i></a> ';

      // SEP link
      if (idea.sep_dir != undefined && idea.sep_dir != '')
      item += '<a href="http://plato.stanford.edu/entries/' + idea.sep_dir + '" data-toggle="tooltip" title="'+idea.label+' on the Stanford Encyclopedia of Philosophy" data-placement="right" class="pull-right"><img src="/img/sepmanicon.png" class="pull-right" /></a>';
      else item += '<img src="/img/empty.gif" class="pull-right" width="16" />';

      // Wiki link
      if (idea.wiki != undefined && idea.wiki != '')
        item += '<a href="http://wikipedia.org/wiki/' + idea.wiki + '" class="pull-right" data-toggle="tooltip" title="'+idea.label+' on Wikipedia"><img src="/img/wikiicon.png" class="pull-right" /></a>';
      else item += '<img src="/img/empty.gif" class="pull-right" width="16" />';


      item += '<a href="' + idea.url + '" data-toggle="tooltip" title="'+idea.label+' on InPhO">' + idea.label + '</a>';
      item += '</li>';
      $('#' + attr + ' ol .more').before(item);
      $('#'+attr+' [data-toggle="tooltip"]').tooltip();
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
