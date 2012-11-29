var w = 960;
var h = 600;
var root;
var i = 0;

var tree = d3.layout.tree()
  .size([h, w - 160]);

var diagonal = d3.svg.diagonal()
  .projection(function(d) { return [d.y, d.x]; });

var vis = d3.select("#chart").append("svg")
  .attr("width", w)
  .attr("height", h)
  .append("g")
  .attr("transform", "translate(80, 0)");

d3.json("/inpho.json", function(json) {

  root = json;
  root.x0 = 0;
  root.y0 = 0;

  function toggleAll(d) {
    if (d.children) {
      d.children.forEach(toggleAll);
      toggle(d);
    }
  }

  root.children.forEach(toggleAll);
  update(root);
  $('#chart .node:not(#demoNode)').click(function() {$('#chart .alert').hide()});
});


var filling = function(d) { return d._children ? "lightsteelblue" : "#fff"; };

function update(source) {
  var duration = d3.event && d3.event.altKey ? 5000 : 500;
  var nodes = tree.nodes(root).reverse();
  nodes.forEach(function(d) { d.y = d.depth * 180; });




  /***  NODE HANDLING  ***/
  var node = vis.selectAll("g.node")
    .data(nodes, function(d) {
      return d.id || (d.id = ++i);
    });

  // Enter in any newfound nodes at parent's previous position.
  var nodeEnter = node.enter().append("svg:g")
    .attr("class", "node")
    .attr("transform", function(d) {
      return "translate(" + source.y0 + "," + source.x0 + ")";
    });

  // Draw a circle for each newly-found node.
  nodeEnter.append("svg:circle")
    .attr("r", 4.5)
    .style("fill", filling)
    .on("click", function(d) {
      toggle(d);
      update(d);
    });

  // Draw a label for each newly-found node.
  nodeEnter.append("svg:a")
    .attr("xlink:href", function(d) { return window.location.protocol + "//" + window.location.host + d.url; })
    .append("svg:text")
    .attr("dx", function(d) {
      return d.children || d._children ? -8 : 8;
    })
    .attr("dy", 3)
    .attr("text-anchor", function(d) {
      return d.children || d._children ? "end" : "start";
    })
    .text(function(d) {
      return d.name;
    })
    .on("click", function(d) {
      document.location.href=(window.location.protocol + "//" + window.location.host + d["url"]);
    });

  //Transition nodes to their new positions.
  var nodeUpdate = node.transition()
    .duration(duration)
    .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

  nodeUpdate.select("circle")
    .style("fill", filling);

  nodeUpdate.select("text")
    .style("fill-opacity", 1);

  // remove any exiting nodes.
  var nodeExit = node.exit().transition()
    .duration(duration)
    .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
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
    .attr("class", "link")
    .attr("d", function(d) {
      var o = {x: source.x0, y: source.y0};
      return diagonal({source: o, target: o});
    })
    .transition()
    .duration(duration)
    .attr("d", diagonal);

  // Transition links to their new positions.
  link.transition()
    .duration(duration)
    .attr("d", diagonal);

  // remove any exiting links.
  link.exit().transition()
    .duration(duration)
    .attr("d", function(d) {
      var o = {x: source.x, y: source.y };
      return diagonal({source: o, target: o});
    })
    .remove();

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
