(function() {
  'use strict';

  fetch(`/api/namespaces/${NAMESPACE_ID}`)
    .then( resp =>  resp.json() )
    .then( result => {
      console.log(result);
      init(result[0]);
    });

  function init(data) {
    let records = data.items.map( (v, i) => {
      return {
        recid: v.taicol_usage_id,
        scientificName: v.scientificName,
        commonNames: v.commonNames.join(','),
        synonyms: v.synonyms.map( x => (`${x[0]} (${x[1]})`)).join('\n'),
        description: v.addFields.description || '',
      };
    });

    let layout = new w2layout({
      name: 'layout',
      box: '#layout',
      padding: 4,
      panels: [
        { type: 'left', size: '50%', resizable: true},
        { type: 'main', resizable: true, style: 'overflow: hidden'},
      ]
    });

  let gridConfig = {
    name: 'grid',
    header: `${data.title} | ${data.author}`,
    reorderRows: false,
    multiSelect: false,
    show: {
        header: true,
        footer: true,
    },
    columns: [
      { field: 'recid', text: 'ID', size: '70px'},
      { field: 'scientificName', text: 'Scientific Name', size: '60%'},
      { field: 'commonNames', text: 'Common Name', size: '20%'},
    ],
    records: records,
    onClick(event) {
      event.done(() => {
        let sel = this.getSelection();
        if (sel.length == 1) {
          w2ui.form.recid = sel[0];
          w2ui.form.record = w2utils.extend({}, this.get(sel[0]));
          w2ui.form.refresh();
        } else {
          w2ui.form.clear()
        }
      });
    },
  };

    let formConfig = {
      header: 'Detail',
      name: 'form',
      fields: [
        {
          field: 'recid',
          type: 'text',
          html: {
            label: 'ID',
            attr: 'size="10"',
          }
        }, {
          field: 'scientificName',
          type: 'text',
          html: {
            label: 'Scientific Name',
            attr: 'size="40"',
          }
        }, {
          field: 'commonNames',
          type: 'text',
          html: {
            label: 'Common Names',
            attr: 'size="40"',
          }
        }, {
          field: 'synonyms',
          type: 'textarea',
          html: {
            label: 'Synonyms',
          }
        }, {
          field: 'description',
          type: 'textarea',
          html: {
            label: 'Description',
          }
        }
      ],
    };
    let grid = new w2grid(gridConfig);
    let form = new w2form(formConfig);
    layout.html('left', grid);
    layout.html('main', form);
  }

  function init2(data) {
    let records = data.items.map( (v, i) => {
      return {
        recid: v.taicol_usage_id,
        scientificName: v.scientificName,
        commonNames: v.commonNames.join(','),
        synonyms: v.synonyms.map( x => (`${x[0]} (${x[1]})`)).join(','),
        description: v.addFields.description || '',
      };
    });

    let grid = new w2grid({
      name: 'grid1',
      box: '#grid1',
      header: `${data.title} | ${data.author}`,
      show: { header: true },
      columns: [
        { field: 'recid', text: 'ID', size: '50px'},
        { field: 'scientificName', text: 'Scientific Name', size: '60%'},
        { field: 'commonNames', text: 'Common Name', size: '30%'},
        /*{ field: 'synonyms', text: 'Synonyms', size: '40%' },*/
      ],
      records: records,
      onClick(event) {
        let record = this.get(event.detail.recid)
        grid2.clear()
        grid2.add([
          { recid: 0, name: 'ID:', value: record.recid },
          { recid: 1, name: 'Scientific Name:', value: record.scientificName },
          { recid: 2, name: 'Common Names:', value: record.commonNames },
          { recid: 3, name: 'Synonyms:', value: record.synonyms },
          { recid: 3, name: 'Description:', value: record.description },
        ]);
      }
    });
    /*
    let grid2 = new w2grid({
      name: 'grid2',
      box: '#grid2',
      header: 'Details',
      show: { header: true, columnHeaders: false ,toolbar: true},
      name: 'grid2',
      columns: [
        { field: 'name', text: 'Name', size: '160px', style: 'background-color: #efefef; border-bottom: 1px solid white; padding-right: 5px;', attr: "align=right" },
        { field: 'value', text: 'Value', size: '100%' }
      ]
      });
      */
  }
})();
