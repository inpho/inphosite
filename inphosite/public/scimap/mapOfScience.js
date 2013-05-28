/**
 * mapOfScience.js
 *
 * Samuel Waggoner
 * srwaggon@indiana.edu / Samuel.Waggoner@gmail.com
 * 2/22/2013
 *
 * Generates Katy Borner's Map of Science using
 * mbostock's D3js
 *
 */

// observed from dataset
var minNodeX = 100;
var maxNodeX = 500;
var minNodeY = 100;
var maxNodeY = 350;

var xScale = 940 / maxNodeX;
var yScale = 600 / maxNodeY;

var xOffset = -80 * xScale; // Represents the difference between the window pane's (0,0) and the graph's (0,0)
var yOffset = -80 * yScale; 

var color = {
  "Blue":d3.rgb("#0000FF"),
  "OliveGreen":d3.rgb("#AEB05D"),
  "Canary":d3.rgb("#FDB813"),
  "Peach":d3.rgb("#FFCC99"),
  "Dandelion":d3.rgb("#F0E130"),
  "Mahogany":d3.rgb("#670A0A"),
  "Lavender":d3.rgb("#E6E6FA"),
  "SkyBlue":d3.rgb("#87CEEB"),
  "Mulberry":d3.rgb("#C54B8C"),
  "BrickRed":d3.rgb("#841F27"),
  "Yellow":d3.rgb("#FFFF00"),
  "Emerald":d3.rgb("#55D43F"),
  "Red":d3.rgb("#FF0000")
}


var weightSlider = d3.select("#weightSlider");

weightFilter = function(data) {
  return data.group === 1 || data._size >= weightSlider.property("value");
};

weightSlider.on("change", function(event) {
  applyFilter(weightFilter);
});

$("#btnScience").click( function(event) {
  fullGraph.nodes.forEach( function(d) {
    d._size = d.xfact;  
  });
  applyFilter(weightFilter);
  redraw(0, xScale, yScale);
});


var chart = d3.select("#chart")

var svg = chart.append("svg")
  .attr("width", 940)
  .attr("height", 600 * .8);

var force = d3.layout.force()
  .charge(0) // might be important.. 
  .size([940 * xScale, 600 * yScale]);

var fullGraph;


// Must load original graph before 
d3.json("/scimap/mapOfScienceData.json", function(error, data) {
//d3.json("small-data.json", function(error, data) {
  fullGraph = data;//d3.map(data);
  force = force
    .nodes(data.nodes)
    .links(data.links)
    .start()
    .stop();

  // Request additional data set with area count for each science.

  d3.csv("num_areas.csv", function(error, response) {
    areaCount = {};
    response.forEach( function(d) { 
      areaCount[parseInt(d["sub_discipline_Id"])] = parseInt(d["num_areas"]);
    });

    // Give each node a num_areas attribute.
    // Give each node a size based on num_areas.
    fullGraph.nodes.forEach( function(d) {
      count = areaCount[d.id] || 1;
      d.num_areas = count;
      d._size = d.num_areas;
    });
    applyFilter(weightFilter);
    redraw(0, xScale, yScale);
  });

  
  // Enable Scale Behaviour (mousewheel scroll)
  // TODO: Get this to zoom centered on mouse location.
  svg.call(d3.behavior.zoom()
           .on("zoom", function() {
             var event = d3.event.sourceEvent;

             if (event.type=='mousewheel' || event.type=='DOMMouseScroll') {
               var wheelDelta = event.wheelDelta;
               var delta = parseInt(wheelDelta / 100) * 0.5;
               if (xScale + delta > 0 && yScale + delta > 0) {
                 xScale += delta;
                 yScale += delta;
               }
               redraw(500, xScale, yScale);
             }}));
  
  // Enable drag behaviour.
  svg.call(d3.behavior.drag()
           .on("drag", function() {
             xOffset += d3.event.dx;
             yOffset += d3.event.dy;
             redraw(0, xScale, yScale);
           }));

  buildGraph(data);
});



function buildGraph(graph) {
  /** Perform the join, render the data, and then adds labels. **/
  updateLinks(graph.links);
  updateNodes(graph.nodes);

  var node = svg.selectAll(".node")
    .data(graph.nodes, function(d) {
      return d.name;
    });

  // text label nodes
  node.filter( function(d) { return d.group === 1; })
    .append("text")
    .attr("dx", "1em")
    .attr("dy", ".5em")
    .style("stroke", function(d) { return color[d.color].darker(2); })
    .style("text-anchor", "start")
    .text( function(d) { return d.name; });
  
  node.append("title").text(function(d) { return d.name; });
}



function updateNodes(nodeData) {
 var node = svg.selectAll(".node") // set comparison
    .data(nodeData, function(d) {
      return d.id;
    });

  var nodeEnter = node.enter()   // introduce new
    .append("g")
    .attr("class", "node")
    .attr("transform", function(d) {
      return "translate(" + (d.x * xScale + xOffset) + "," + (d.y * yScale + yOffset) + ")";
    }).append("circle")
    .attr("r", function(d) { return d._size; })
    .style("fill", function(d) { return color[d.color]; });

  var nodeUpdate = node   // update existing
    .attr("transform", function(d) {
      return "translate(" + (d.x * xScale + xOffset) + "," + (d.y * yScale + yOffset) + ")";
    })
    .select("circle")
      .attr("r", function(d) { return d._size; });


  var nodeExit = node.exit().remove();   // remove expiring
}



function updateLinks(linkData) {
  /** Called whenever link data changes. Performs a join. **/

  var link = svg.selectAll(".link") // set comparison
    .data(linkData, function(d) {
      return "" + d.source.name + d.target.name;
    });

  var linkEnter = link.enter()   // introduce new
    .insert("line",":first-child")
    .attr("class", "link")
    .style("stroke-width", function(d) { return Math.sqrt(Math.sqrt(Math.sqrt(d.weight))); })
    .style("stroke", function(d) { if (d.source.color === d.target.color) {
      return color[d.source.color];} else { return "#ccc"; } });

  var linkUpdate = link   // update existing
    .attr("x1", function(d) { return d.source.x * xScale + xOffset; })
    .attr("y1", function(d) { return d.source.y * yScale + yOffset; })
    .attr("x2", function(d) { return d.target.x * xScale + xOffset; })
    .attr("y2", function(d) { return d.target.y * yScale + yOffset; });
  
  var linkExit = link.exit().remove();   // remove expiring
}



function redraw(transitionDuration, xScale, yScale) {
  /** Called to redraw the graph. **/
  
  var link = svg.selectAll(".link");
  var node = svg.selectAll(".node");
  
  var linkUpdate = link.transition().duration(transitionDuration)
    .attr("x1", function(d) { return d.source.x * xScale + xOffset; })
    .attr("y1", function(d) { return d.source.y * yScale + yOffset; })
    .attr("x2", function(d) { return d.target.x * xScale + xOffset; })
    .attr("y2", function(d) { return d.target.y * yScale + yOffset; });
  
  var nodeUpdate = node.transition().duration(transitionDuration)
    .attr("transform", function(d) { return "translate(" + (d.x * xScale + xOffset) + "," + (d.y * yScale + yOffset) + ")"; });
}



function applyFilter(filter) {
  
  updateLinks(fullGraph.links.filter(
    function(d) {
      return filter(d.source) && filter(d.target);
    }));
  
  updateNodes(fullGraph.nodes.filter(
    function(d) {
      return filter(d);
    }));
  
}



window.onresize = function(event) {

  svg.attr("width", window.innerWidth * .95)
    .attr("height", window.innerHeight * .93);

  xScale = window.innerWidth / maxNodeX;
  yScale = window.innerHeight / maxNodeY;

  redraw(0, xScale, yScale);
}

