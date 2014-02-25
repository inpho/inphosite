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
        + ' <a onClick="inpho.tabnav.appendTab(\'tabnav\', \'i'+ idea.ID +'\', \''+ idea.label + '\', \'/entity/' + idea.ID + '/panel/' + id + '\')" href="#i'+ idea.ID + '" data-toggle="tab" class="tablink"><i class="icon-search"></i></a> ';

      // SEP link
      if (idea.sep_dir != undefined && idea.sep_dir != '')
        item += '<a href="http://plato.stanford.edu/entries/' + idea.sep_dir + '"><img src="/img/sepmanicon.png" class="pull-right" /></a>';
      else item += '<img src="/img/empty.gif" class="pull-right" width="16" />';

      // Wiki link
      if (idea.wiki != undefined && idea.wiki != '')
        item += '<a href="http://wikipedia.org/wiki/' + idea.wiki + '"><img src="/img/wikiicon.png" class="pull-right" /></a>';
      else item += '<img src="/img/empty.gif" class="pull-right" width="16" />';


      item += '<a href="' + idea.url + '">' + idea.label + '</a>';
      item += '</li>';
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

inpho.entity.showMoreMustache = function (attr, parent_id, type, limit, alt_title, statistical) {
  // set default values for variables if values are not passed in.
  if (!alt_title)
      var alt_title = null; 
  if (!limit)
      var limit = 10;
  if (!statistical)
      var statistical = false;
  if (!type)
    var type = "idea"; 
  
  // build url to grab attribute
  var url = "/" + type + "/" + parent_id + "/" + attr + ".json?limit=" + limit;
  var more = "";

  // get attribute data
  return $.getJSON(url, function (data) {
    $.get('../templates/printList.mustache', function(template) {
      // append each item to the list
      if (data.responseData.total > limit) {
        more += "<li class='more'><a Onclick=\"inpho.entity.showMoreMustache('" + attr + "', '" + parent_id + "', '" + type + "', " + (limit + 10) + ", " + alt_title + ", '" + statistical + "')\">Show more... (" + (data.responseData.total - limit) + ")</a></li>";
      }

      var json = {
                    "attr": attr,
                    "parent_id": parent_id,
                    "type": type,
                    "alt_title": alt_title,
                    "new_limit": limit+10,
                    "statistical": statistical,
                    "more": more,
                    "results": data.responseData.results
                 };
      var html = Mustache.to_html(template, json);// set item as printList.mustache template in the public/template directory

      $('#'+attr).html(html);
    });
  });
}
