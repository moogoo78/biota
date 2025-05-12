(function() {
  'use strict';

  const downloadDocx = document.getElementById('download-docx');

  downloadDocx.onclick = (e) => {
    e.preventDefault();

    const paramsString = window.location.search;
    const searchParams = new URLSearchParams(paramsString);

    const namespaceIds = searchParams.get('namespace_ids');

    fetch('/api/publish', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        namespaceIds: namespaceIds,
        format: 'docx',
      })
    })
      .then(resp => resp.blob())
      .then(result => {
        //console.log(result);
        var file = window.URL.createObjectURL(result);
        window.location.assign(file);
      });
  };

  const itemNames = document.getElementsByClassName('item-names');
  for (let x of itemNames) {
    x.onclick = (e) => {
      e.preventDefault();
      const q = e.target.dataset.q;
      const source = e.target.dataset.source;
      handleNameClick(q, source);
      /*
      fetch(`https://api.gbif.org/v1/species/search?q=${q}&rank=SPECIES&datasetKey=d7dddbf4-2cf0-4f39-9b2a-bb099caae36c`)
        .then(resp => resp.json())
        .then(result => {
          console.log(result);
          w2popup.open({
            title: `GBIF backbone: ${q}`,
            width: 800,
            height: 400,
            showMax: true,
            body: '<div id="popup-grid" style="position: absolute; left: 0px; top: 0px; right: 0px; bottom: 0px;"></div>'
          })
            .then(() => {
              console.log('ok');
              let taxonGrid = new w2grid({
                name: 'popup-grid',
                box: '#popup-grid',
                style: 'border: 0px; border-left: 1px solid #efefef',
                url: `/api/data/${k}`,
                columns: [
                  { field: 'key', text: 'taxonKey', size: '80px' },
                  { field: 'scientificName', text: 'Scientific Name', size: '250px' },
                  { field: 'status', text: 'Status', size: '80px' },
                  { field: 'accordingTo', text: 'According To', size: '280px', attr: 'align="center"' }
                ],
                onClick(event) {
                  let record = this.get(event.detail.recid);
                  console.log(record);
                  taxonGrid.destroy();

                  fetch(`https://api.gbif.org/v1/occurrence/search?basisOfRecord=PreservedSpecimen&taxon_key=${record.key}`)
                    .then(resp => resp.json())
                    .then(result => {

                      let spGrid = new w2grid({
                        name: 'popup-grid',
                        box: '#popup-grid',
                        style: 'border: 0px; border-left: 1px solid #efefef',
                        columns: [
                          { field: 'recordedBy', text: 'Collector', size: '100px' },
                          { field: 'recordNumber', text: 'Coll. Number', size: '80px' },
                          { field: 'country_code', text: 'Country', size: '40px' },
                          { field: 'locality', text: 'Locality', size: '250px' },
                          { field: 'county', text: 'County', size: '120px' },
                          { field: 'institution', text: 'Institution', size: '100px'},
                          { field: 'catalogNumber', text: 'Catalog Number', size: '180px' },
                        ],
                      });
                      let data = result.results.map((v, i) => {
                        console.log(v);
                        return {
                          recid: i,
                          country_code: v.countryCode,
                          locality: v.locality,
                          county: v.county || '',
                          institution: v.institutionCode,
                          catalogNumber: v.catalogNumber,
                          recordNumber: v.recordNumber,
                          recordedBy: v.recordedBy,
                        };
                      });
                      spGrid.add(data);
                    });
                }
              });

              let records = result.results.map( (v, i) => {
                console.log(v);
                let sciName = v.species;
                if (v.authorship) {
                  sciName = `${sciName} ${v.authorship}`;
                }
                return {
                  recid: i,
                  key: v.speciesKey,
                  scientificName: sciName,
                  accordingTo: v.accordingTo,
                  status: v.taxonomicStatus,
                };
              });
              taxonGrid.add(records);
              });

              });
      */
    };

  } // end of itemNames iter

  function renderSpecimenGrid (record) {
    let spGrid = new w2grid({
      name: 'popupgrid',
      box: '#popup-grid',
      style: 'border: 0px; border-left: 1px solid #efefef',
      show: {
        footer: true,
        //toolbar: true,
      },
      columns: [
        { field: 'recordedBy', text: 'Collector', size: '100px' },
        { field: 'recordNumber', text: 'Coll. Number', size: '80px' },
        { field: 'country_code', text: 'Country', size: '40px' },
        { field: 'locality', text: 'Locality', size: '250px' },
        { field: 'county', text: 'County', size: '120px' },
        { field: 'institution', text: 'Institution', size: '100px'},
        { field: 'catalogNumber', text: 'Catalog Number', size: '180px' },
      ],
      onRequest: function(event) {
        console.log('-- server call --');
        console.log(event);
      }
    });
    const params = {
      limit: 5,
      offset: 0,
      basisOfRecord: 'PreservedSpecimen',
      taxon_key: record.key,
    };
    //spGrid.request('get-records', params, 'https://api.gbif.org/v1/occurrence/search', (e) => {
    //  console.log('cb', e);
    //});
  }
    /*
    function(event)  {
        event.preventDefault();
        console.log(event);
        console.log('load', this);
        w2utils.lock(this.box, 'Loading data from GBIF...', true);

      }

  }
    */
    /*
    spGrid.load(`https://api.gbif.org/v1/occurrence/search?basisOfRecord=PreservedSpecimen&taxon_key=${record.key}&limit=100&offset=0`, (result) => {
      console.log(result);
      let data = result.results.map((v, i) => {
        console.log(v);
        return {
          recid: i,
          country_code: v.countryCode,
          locality: v.locality,
          county: v.county || '',
          institution: v.institutionCode,
          catalogNumber: v.catalogNumber,
          recordNumber: v.recordNumber,
          recordedBy: v.recordedBy,
        };
      });
      spGrid.add(data);
      });
      */
//}
function fetchGBIFData(params) {
    // Build query string from params
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        queryParams.append(key, value);
    });
    
    // GBIF Occurrence API endpoint
    const apiUrl = `https://api.gbif.org/v1/occurrence/search?${queryParams.toString()}`;
    
    // Fetch with proper headers
    return fetch(apiUrl, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`GBIF API responded with status: ${response.status}`);
        }
        return response.json();
    });
}
  function handleNameClick(q, source) {
    let sourceLabel = '';
    let sourceAPI = '';
    if (source === 'gbif') {
      sourceLabel = 'GBIF backbone';
      sourceAPI = `https://api.gbif.org/v1/species/search?q=${q}&rank=SPECIES&datasetKey=d7dddbf4-2cf0-4f39-9b2a-bb099caae36c`;
    } else if (source === 'taicol') {
      sourceLabel = 'TaiCOL';
      //sourceAPI = `https://api.taicol.tw/v2/taxon?scientific_name=${q}`;
      sourceAPI = `/api/external/names/${q}?source=taicol`;
    }
    w2popup.open({
      title: `${sourceLabel}: ${q}`,
      width: 1000,
      height: 600,
      showMax: true,
      body: '<div style="position: relative; height: 300px;"><div id="grid1" style="display: inline-block; width: 1000px; height: 150px;"></div><div id="grid2" style="display: inline-block; width: 1000px; height: 400px;"></div></div>',
    })
      .then(() => {
        let grid = new w2grid({
          name: 'grid1',
          box: '#grid1',
          header: 'Available Scientific Names',
          show: { header: true, footer: true },
            columns: [
              { field: 'key', text: 'taxonKey', size: '80px' },
              { field: 'scientificName', text: 'Scientific Name', size: '250px' },
              { field: 'status', text: 'Status', size: '80px' },
              { field: 'accordingTo', text: 'According To', size: '280px', attr: 'align="center"' }
            ],
          onClick(event) {
            const record = grid.get(event.detail.recid);
            //w2ui['grid2'].request();
            let grid2 = new w2grid({
              name: 'grid2',
              box: '#grid2',
              header: 'Found Specimens',
              show: { header: true , footer: true},
              url: `/api/external/gbif-occurrences/${record.key}`,
              autoLoad: false,
              columns: [
                { field: 'recordedBy', text: 'Collector', size: '120px' },
                { field: 'recordNumber', text: 'Coll. Number', size: '60px' },
                { field: 'country_code', text: 'Country', size: '40px' },
                { field: 'locality', text: 'Locality', size: '250px' },
                { field: 'county', text: 'County', size: '120px' },
                { field: 'institution', text: 'Institution', size: '100px'},
                { field: 'catalogNumber', text: 'Catalog Number', size: '180px' },
              ],
              onClick(event) {
              },
            });
          },
         });
        grid.load(sourceAPI, (result) => {
          console.log(result);
            let records = result.results.map( (v, i) => {
              let sciName = v.scientificName;
              if (v.authorship) {
                sciName = `${sciName} ${v.authorship}`;
              }
              return {
                recid: i,
                key: v.speciesKey,
                scientificName: sciName,
                accordingTo: v.accordingTo,
                status: v.taxonomicStatus,
              };
            });
          grid.add(records);
        });
      }).close((e) => {
        w2ui['grid1'].destroy();
        w2ui['grid2'].destroy();
      }); // end of popup then
  }
})();
