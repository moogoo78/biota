(function() {
  'use strict';

  let recordMap = {
    specimen: {},
    distribution: [],
  }
  fetch(`/api/namespaces/${NAMESPACE_ID}`)
    .then( resp =>  resp.json() )
    .then( result => {
      console.log(result);
      init(result[0]);
    });

  async function findSpecimen(recid, q, nameid) {
    const resp = await fetch(`/api/external/names/taicol/[${nameid}]${q}`);
    const result = await resp.json();
    if (result.records.length > 0) {
      const taxonKey = result.records[0].key;
      console.log('get taxonKey:', taxonKey);
      const resp2 = await fetch(`/api/external/data/tbia/${taxonKey}`);
      const result2 = await resp2.json();
      console.log(result2);
      w2popup.open({
        title   : `TBIA Specimens: ${q}`,
        body    : '<div id="gridx" style="width: 100%; height: 100%;"></div>',
        style   : 'padding: 15px 0px 0px 0px',
        width   : 940,
        height  : 600,
        //showMax : true,
        async onToggle(event) {
          await event.complete
          w2ui.relForm.resize();
        }
      })
        .then((event) => {
          let  gridxconf = {
            name: 'gridx',
            box: '#gridx',
            multiSelect: true,
            show: { selectColumn: true },
            style: 'border: 1px solid #efefef',
            columns: [
              { field: 'institutionCode', text: 'Institution Code', size: '30px' },
              { field: 'catalogNumber', text: 'Catalog Number', size: '80px' },
              { field: 'recordedBy', text: 'Collector', size: '120px' },
              { field: 'recordNumber', text: 'Coll. Number', size: '80px' },
              { field: 'date', text: 'Date', size: '80px' },
              { field: 'locality', text: 'Locality', size: '250px' },
              { field: 'datasetTitle', text: 'Dataset', size: '150px'},
              { field: 'remarks', text: 'remarks', size: '200px' },
              { field: 'media', text: 'media', size: '100px',
                render: function (record, extra) {

                  // HACK distribution
                  if ('adm2' in record.named_areas && recordMap[record.recid].distribution.indexOf(record.named_areas.adm2) < 0) {
                    recordMap[record.recid].distribution.push(record.named_areas.adm2);
                  }
                  let d = document.getElementById('summary-distribution');
                  d.textContent = `分布縣市: ${summaryDistribution.join('|')}`;

                  let mlist = record.media.map( x => {
                    return `<img src="${x}" height="50" />`;
                  });
                  return `<div>${mlist}</div>`;
                }
              },
              { field: 'url', text: 'Link', size: '40px',
                render: function (record) {
                  return `<a href="${record.url}" target="_blank">go</a>`;
                }
              }
            ],
            records: result2.records,
            async onClick(event) {
              await event.complete // needs to wait for evnet complete cycle, so selection is right
              let sel = this.getSelection();
              console.log(sel, recid);
              recordMap[recid].specimen = sel.map( (x) => {
                return result2.records[x];
              });
            }
          };
          let gridx = new w2grid(gridxconf);
        });
    }
  }

  function init(data) {
    let records = data.items.map( (v, i) => {
      return {
        recid: v.taicol_usage_id,
        scientificNameID: v.taicol_taxon_name_id,
        scientificName: v.scientificName,
        commonNames: v.commonNames.join(','),
        synonyms: v.synonyms.map( x => (`${x[0]} (${x[1]})`)).join('\n'),
        description: v.addFields.description || '',
        referenceTitle: v.reference_title,
        referenceName: v.reference_name,
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
      { field: 'recid', text: 'ID', size: '60px'},
      { field: 'scientificName', text: 'Scientific Name', size: '35%'},
      { field: 'commonNames', text: 'Common Name', size: '10%'},
      { field: 'referenceName', text: 'Reference', size: '35%'},
    ],
    records: records,
    onClick(event) {
      event.done(() => {
        let sel = this.getSelection();
        if (sel.length == 1) {
          w2ui.form.recid = sel[0];
          w2ui.form.record = w2utils.extend({}, this.get(sel[0]));
          if (recordMap[sel[0]]?.specimen) {
            w2ui.form.setValue('specimens', recordMap[sel[0]]);
          }
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
      toolbar: {
        items: [{
          id: 'form-toolbar-find',
          type: 'button',
          text: 'search TBIA for Specimens',
          img: 'w2ui-icon-info',
        }],
        onClick(event) {
          if (event.target === 'form-toolbar-find') {
            const nameID = w2ui.form.getValue('scientificNameID')
            const scName = w2ui.form.getValue('scientificName');
            const recid = w2ui.form.getValue('recid');
            findSpecimen(recid, scName, nameID);
          }
        }
      },
      fields: [{
        field: 'recid',
        type: 'text',
        html: {
          label: 'Namespace Usage ID',
          attr: 'size="10"',
        }
      }, {
        field: 'scientificNameID',
        type: 'text',
        html: {
          label: 'TaxonNameID',
          attr: 'size="10"',
        }
      }, {
        field: 'scientificName',
        type: 'text',
        html: {
          label: 'Scientific Name',
          attr: 'size="60"',
        }
      }, {
        field: 'referenceTitle',
        type: 'text',
        html: {
          label: 'Reference Title',
          attr: 'size="60"',
        }
      }, {
        field: 'referenceName',
        type: 'text',
        html: {
          label: 'Reference Name',
          attr: 'size="60"',
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
          attr: 'rows="3" cols=40'
        }
      }, {
        field: 'description',
        type: 'textarea',
        html: {
          label: 'Description',
          attr: 'rows="12" cols=40'
        }
      }, {
        field: 'specimens',
        type: 'textarea',
        html: {
          label: 'Specimens',
          attr: 'rows="2" cols=40 readonly'
        }
      }, {
        field: 'distribution',
        type: 'textarea',
        html: {
          label: 'Distribution',
          attr: 'rows="2" cols=40 readonly'
        }
      }],
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
