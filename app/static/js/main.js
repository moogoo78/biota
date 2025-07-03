(function() {
  'use strict';

  let currentSelect = {
    schema: null,
    records: null,
  };

  // init layout
  let layout = new w2layout({
    name: 'layout',
    padding: 0,
    panels: [
      { type: 'left', size: 200, resizable: true, minSize: 120 },
      { type: 'main', minSize: 550, overflow: 'hidden' }
    ]
  });

  layout.render('#main');

  // get taicol schema
  fetch('/api/schema')
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      const layout = w2ui['layout'];
      //console.log(data);
      let nodes = [];
      let grids = {};
      for (const [k, v] of Object.entries(data)) {
        nodes.push({
          id: k,
          text: k,
          icon: 'fa fa-list-alt',
          selected: null,/*(i === 0) ? true : null,*/
        });
        nodes.push({ id: 'tree', text: 'Taxon Tree', icon: 'fa fa-share-alt' });
        grids[k] = new w2grid({
          name: k,
          url: `/api/data/${k}`,
          columns: v.map( x => ({field: x, text: x})),
          show: {
            toolbar: true,
            footer: true,
            toolbarColumns: true,
            selectColumn: true,
          },
          multiSelect: false,
          autoLoad: false,
          toolbar: {
            items: [
              { type: 'break' },
              //{ type: 'button', id: 'mybutton-docx', text: 'export docx', icon: 'fa fa-folder' },
              { type: 'button', id: 'mybutton-content', text: 'Select Namespace', icon: 'fa fa-bolt' },
            ],
            onClick: function (target, data) {
              console.log(target, data);
              switch (target) {
              case 'mybutton-content':
                if (currentSelect.records.length > 0) {
                  const ids = currentSelect.records.join(',');
                  //window.open(`/preview?namespace_ids=${ids}`, '_blank').focus();
                  window.open(`/preview2/${ids}`, '_blank').focus();
                }
                break;
              }
              // console.log(currentSelect);
              // if (currentSelect.schema === 'my_namespaces' && currentSelect.record) {
              //   fetch('/api/pub', {
              //     method: 'POST',
              //     headers: {
              //     'Content-Type': 'application/json'
              //     },
              //     body: JSON.stringify({
              //       namespace_id: currentSelect.record.id
              //     })
              //   })
              //     .then(resp => resp.json())
              //     .then(result => {
              //       console.log(result);
              //     });
              //     }
            }
          },
          // dblClick(recid, event) {
          //   showContent([recid]);
          // },
          async onSelect(event) {
            await event.complete;
            //console.log('select', event.detail, this.getSelection())
            currentSelect.records = this.getSelection();
          },
        });
      } // end of for

      let sidebar = new w2sidebar({
        name: 'sidebar',
        nodes: [
          { id: 'general', text: 'Sources', group: true, expanded: true, nodes: nodes},
        ],
        onClick(event) {
          if (event.target === 'tree') {
            layout.html('main', '<div style="padding: 10px"><div id="container"></div></div>');
// Declare the chart dimensions and margins.
const width = 640;
const height = 400;
const marginTop = 20;
const marginRight = 20;
const marginBottom = 30;
const marginLeft = 40;

// Declare the x (horizontal position) scale.
const x = d3.scaleUtc()
    .domain([new Date("2023-01-01"), new Date("2024-01-01")])
    .range([marginLeft, width - marginRight]);

// Declare the y (vertical position) scale.
const y = d3.scaleLinear()
    .domain([0, 100])
    .range([height - marginBottom, marginTop]);

// Create the SVG container.
const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

// Add the x-axis.
svg.append("g")
    .attr("transform", `translate(0,${height - marginBottom})`)
    .call(d3.axisBottom(x));

// Add the y-axis.
svg.append("g")
    .attr("transform", `translate(${marginLeft},0)`)
    .call(d3.axisLeft(y));

// Append the SVG element.
            const container = document.getElementById('container');
            container.append(svg.node());
          } else {
            const schema = event.target;
            grids[schema].clear();
            layout.html('main', grids[schema]);
            currentSelect.schema = schema;
            currentSelect.record = null;
          }
        }
      });
      layout.html('left', sidebar);
    })
    .catch(error => {
      console.error('Error fetching layout config:', error);
    });

})();
