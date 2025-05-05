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
          multiSelect: true,
          autoLoad: false,
          toolbar: {
            items: [
              { type: 'break' },
              //{ type: 'button', id: 'mybutton-docx', text: 'export docx', icon: 'fa fa-folder' },
              { type: 'button', id: 'mybutton-content', text: 'show content', icon: 'fa fa-bolt' },
            ],
            onClick: function (target, data) {
              console.log(target, data);
              switch (target) {
              case 'mybutton-content':
                if (currentSelect.records.length > 0) {
                  const ids = currentSelect.records.join(',');
                  window.open(`/preview?namespace_ids=${ids}`, '_blank').focus();
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
          { id: 'general', text: 'Tables', group: true, expanded: true, nodes: nodes}
        ],
        onClick(event) {
          const schema = event.target;
          grids[schema].clear();
          layout.html('main', grids[schema]);
          currentSelect.schema = schema;
          currentSelect.record = null;
        }
      });
      layout.html('left', sidebar);
    })
    .catch(error => {
      console.error('Error fetching layout config:', error);
    });

})();
