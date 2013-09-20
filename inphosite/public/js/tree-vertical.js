var margin = 20
var w = 360;
var h = 600;
var root;
var i = 0;

var tree = d3.layout.tree()
  .size([w, h]);

// custom curve function to create bottom of node to left of node links.
// using string join because JavaScript engines struggle with numbers and
// strings using the + operator. In particular "C" + 25 + " " + 10 ?= "C25010"
var curve = function(d,i) {
  var source =  "M" + d.source.x + "," + d.source.y;
  var c1 = "C" + d.source.x + "," + ((d.source.y + d.target.y) / 2);
  var c2 = (d.source.x + (margin / 5)) + "," + d.target.y;
  var target = d.target.x + "," + d.target.y;
  return [source, c1, c2, target].join(' ');
  }

var vis = d3.select("#chart").append("svg")
  .attr("width", w)
  .attr("height", h)
  .append("g")
  .attr("transform", "translate(" + margin + "," + margin +")");

d3.json("/inpho.json", function(json) {
  root = json;
  root.x0 = 0;
  root.y0 = 0;

  // goes through and selects the proper nodes to disable
  function containsChild(d, ID) {
    if (d.ID == ID) {
      d.selected = true;
      return true;
    } else {
      if (d.children) {
        for(var c=0; c<d.children.length; c++) {
          if (containsChild(d.children[c], ID)) { 
            return true;
          }
        }
      }
      return false;
    }
  }
  function toggleAll(d) {
    var ID = $("#chart").attr('data-selected');

    // recursive call
    if (d.children) {
      d.children.sort(function(a,b){ return (a.name > b.name) ? 1 : -1;});
      d.children.forEach(toggleAll);
    }

    // setting proper appearance
    if (!containsChild(d, ID)) {
      toggle(d);  // doesn't contain child, collapse
    } else if (d.ID == ID) {
      toggle(d); // is the thing, collapse & mark as part of path
      d.partOfPath = true;
    }
    else {
      d.partOfPath = true; // contains child, so part of path
    } 
  }
 
  
  root.partOfPath = true; // root is always part of path

  // toggle nodes and update visualization
  root.children.sort(function(a,b){ return (a.name > b.name) ? 1 : -1;});
  root.children.forEach(toggleAll);
  update(root);
  
});

var filling = function(d) { return d._children ? "lightsteelblue" : "#fff"; };

function update(source) {
  var duration = d3.event && d3.event.altKey ? 5000 : 750;
  var nodes = tree.nodes(root).reverse();
  nodes.forEach(function(d) { d.y = d.depth * 180; });

  var xindent = 20;
  var yindent = 20;
  var j = nodes.length;

  nodes.forEach(function(d) { 
    d.x = xindent * d.depth;
    d.y = yindent * --j;
  });

  d3.select("svg").attr("height", 
    function() { return Math.max(margin + (nodes.length * yindent), d3.select("svg").attr("height")); });
  /***  NODE HANDLING  ***/
  var node = vis.selectAll("g.node")
    .data(nodes, function(d) {
      return d.id || (d.id = ++i);
    });

  // Enter in any newfound nodes at parent's previous position.
  var nodeEnter = node.enter().append("svg:g")
    .attr("class", function (d) { return d.partOfPath ? "node node-path" : "node"})
    .attr("transform", function(d) {
      return "translate(" + source.x0 + "," + source.y0 + ")";
    });

  // Draw a circle for each newly-found node.
  nodeEnter.append("svg:circle")
    .attr("r", 4.5)
    .style("fill", filling)
    .on("click", function(d) {
      toggle(d);
      update(d);
    });

  // Draw alabel for each newly-found node. 

  nodeEnter.append("svg:a")
    .attr("xlink:href", function(d) { return window.location.protocol + "//" + window.location.host + d.url; })
    .append("svg:text")
    .attr("style", function(d) { if (d.selected) return "font-weight: bold;"; else ""; })
    .attr("dx", 8)
    .attr("dy", 3)
    //.attr("fill", "steelblue")
    .attr("text-anchor", "start")
    .text(function(d) {
      return d.name;
    });
    /*
    .on("click", function(d) {
      document.location.href=(window.location.protocol + "//" + window.location.host + d["url"]);
    });*/

  //Transition nodes to their new positions.
  var nodeUpdate = node.transition()
    .duration(duration)
    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")";});
                                     

  nodeUpdate.select("circle")
    .style("fill", filling);

  nodeUpdate.select("text")
    .style("fill-opacity", 1);

  // remove any exiting nodes.
  var nodeExit = node.exit().transition()
    .duration(duration)
    .attr("transform", function(d) { return "translate(" + source.x + "," + source.y + ")"; })
    .remove();

  nodeExit.select("circle")
    .attr("r", 1e-6);

  nodeExit.select("text")
    .style("fill-opacity", 1e-6);
  


  /***  LINK HANDLING  ***/
  var link = vis.selectAll("path.link")
    .data(tree.links(nodes), function(d) { return d.target.id; });

  // Enter any new links at the parent's previous position.
  link.enter().insert("svg:path", "g")
    .attr("class", function(d) { return d.target.partOfPath ? "link link-path" :"link";})
    .attr("d", function(d) {
      var o = {x: source.x0, y: source.y0};
      return curve({source: o, target: o});
    })
    .transition()
    .duration(duration)
    .attr("d", curve);


  // Transition unchanged links to their new positions. 
  link.transition()
    .duration(duration)
    .attr("d", curve);

  // remove any exiting links.
  link.exit().transition()
    .duration(duration)
    .attr("d", function(d) {
      var o = {x: source.x, y: source.y };
      return curve({source: o, target: o});
    })
    .remove();
  //link.exit().remove();

  // selectAll again to correct render order
  // I think this should be possible in a single pass.
  var link = vis.selectAll("path.link")
    .data(tree.links(nodes), function(d) { return d.target.id; })
    .sort(function(a,b) { return (a.target.partOfPath && !b.target.partOfPath) ? 1 : -1 });

  // Stash the old positions for transition.
  nodes.forEach(function(d) {
    d.x0 = d.x;
    d.y0 = d.y;
  });
}


// Toggle children : Set children to null, or to actual children.
function toggle(d) {
  if (d.children) {
    d._children = d.children;
    d.children = null;
  } else {
    d.children = d._children;
    d._children = null;
  }
}
