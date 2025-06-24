(function() {
  'use strict';

  let foundExtension = {};

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

      let summaryDistribution = [];
      result2.records.forEach( record => {
        if ('adm2' in record.named_areas && summaryDistribution.indexOf(record.named_areas.adm2) < 0) {
          summaryDistribution.push(record.named_areas.adm2);
        }
      });

      foundExtension[recid] = {
        specimen: [],
        specimenDisplay: '',
        distribution: summaryDistribution,
      };

      // set form now
      if (summaryDistribution.length > 0) {
        w2ui.form.setValue('distribution', summaryDistribution);
        w2ui.form.refresh();
      }

      w2popup.open({
        title   : `TBIA Specimens: ${q}`,
        body    : '<div id="gridx" style="width: 100%; height: 500px;"></div><div class="w2ui-buttons">',
        style   : 'padding: 15px 0px 0px 0px',
        width   : 1020,
        height  : 600,
        resizable: true, // not work
        //showMax : true,
        async onToggle(event) {
          await event.complete
          w2ui.relForm.resize();
        },
        actions: {
        Ok(event) {
           w2popup.close()
        },
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
              { field: 'media', text: 'media', size: '100px',
                render: function (record, extra) {
                  let mlist = record.media.map( x => {
                    return `<img src="${x}" height="50" class="found-specimen-img"/>`;
                  });
                  return `<div>${mlist}</div>`;
                }
              },
              { field: 'institutionCode', text: 'Institution Code', size: '30px' },
              { field: 'catalogNumber', text: 'Catalog Number', size: '80px' },
              { field: 'recordedBy', text: 'Collector', size: '120px' },
              { field: 'recordNumber', text: 'Coll. Number', size: '80px' },
              { field: 'date', text: 'Date', size: '80px' },
              { field: 'locality', text: 'Locality', size: '250px' },
              { field: 'datasetTitle', text: 'Dataset', size: '150px'},
              { field: 'remarks', text: 'remarks', size: '200px' },
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
              foundExtension[recid].specimen = sel.map( (x) => {
                return result2.records[x];
              });
              if (foundExtension[recid].specimen.length > 0) {
                console.log(foundExtension[recid].specimen);
                //let prettySpecimen = JSON.stringify(foundExtension[recid].specimen, null, 2);
                let prettySpecimen = [];
                for (let i of foundExtension[recid].specimen) {
                  prettySpecimen.push(`${i.specimen_display.county}: ${i.specimen_display.locality}, ${i.recorded_by || '--'} ${i.record_number || '--'}.`);
                }
                let specimenDisplay = prettySpecimen.join(' ');
                foundExtension[recid].specimenDisplay = specimenDisplay;
                w2ui.form.setValue('specimen', specimenDisplay);
                w2ui.form.refresh();
              }
            }
          };
          let gridx = new w2grid(gridxconf);
          let specimenImages = document.getElementsByClassName('found-specimen-img');
          for (let i of specimenImages) {
            i.onclick = function(e) {
              let imgSrc = e.target.src;
              w2popup.message({
                text:`<img src="${imgSrc}" />`,
                width: 1000,
                height: 600,
                hideOn: ['esc', 'click']
              });
            };
          }
        }); // end of w2popup.open then
    }
  }

  function init(data) {
    let records = data.items.map( (v, i) => {
      //console.log(v.item_title.scientific_name);
      //let synonymsList = v.synonyms.map( x => (`${x[0]}`)).join(', ');

      return {
        recid: v.taicol_usage_id,
        scientificNameID: v.taicol_taxon_name_id,
        scientificName: v.item_title.scientific_name.canonical,
        scientificNameAuthor: v.item_title.scientific_name.author,
        commonNames: v.commonNames.join(','),
        synonyms: v.synonyms.map( x => (`${x[0]} (${x[1]})`)).join('\n'),
        //synonymsList: synonymsList,
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
      { field: 'recid', text: 'ID', size: '60px'},
      { field: 'scientificName', text: 'Scientific Name', size: '70%',
        render: function (record) {
          return `<i>${record.scientificName}</i> ${record.scientificNameAuthor}`;
        }
      },
      { field: 'commonNames', text: 'Common Name', size: '20%'},
      //{ field: 'synonymsList', text: 'Synonyms', size: '35%'},
    ],
    records: records,
    onClick(event) {
      event.done(() => {
        let sel = this.getSelection();
        if (sel.length == 1) {
          w2ui.form.recid = sel[0];
          w2ui.form.record = w2utils.extend({}, this.get(sel[0]));

          if (foundExtension[sel[0]]?.specimen.length > 0) {
            //let prettySpecimen = JSON.stringify(foundExtension[sel[0]].specimen, null, 2);
            w2ui.form.setValue('specimen', foundExtension[sel[0].specimenDisplay]);
          }
          if (foundExtension[sel[0]]?.distribution.length > 0) {
            w2ui.form.setValue('distribution', foundExtension[sel[0]].distribution);
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
      actions: {
        custom: {
          text: 'OK',
          class: 'w2ui-btn-blue',
          style: 'text-transform: uppercase',
          onClick(event) {
            w2alert('Custom Action')
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
        field: 'specimen',
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

})();
