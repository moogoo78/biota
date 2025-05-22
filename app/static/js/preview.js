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
      const nameid = e.target.dataset.nameid;
      handleNameClick(source, q, nameid);
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
  function handleNameClick(source, q, nameid) {
    let sourceLabel = '';
    let sourceAPI = `/api/external/names/${source}/${q}`;
    if (source === 'gbif') {
      sourceLabel = 'GBIF backbone';
    } else if (source === 'tbia-taicol') {
      sourceLabel = 'TaiCOL';
      sourceAPI = `/api/external/names/taicol/[${nameid}]${q}`;
    } else if (source === 'tbia-nametool') {
      sourceLabel = 'nametool';
      sourceAPI = `/api/external/names/nametool/[${nameid}]${q}`;
    } else if (source === 'taif') {
      sourceLabel = 'TAIF:';
      sourceAPI = `/api/external/names/pass/${q}`;
    }
    w2popup.open({
      title: `${sourceLabel}: ${q}`,
      width: 1200,
      height: 600,
      showMax: true,
      body: '<div style="position: relative; height: 300px;"><div id="grid1" style="display: inline-block; width: 1200px; height: 150px;"></div><div id="grid2" style="display: inline-block; width: 1200px; height: 400px;"></div></div>',
    })
      .then(() => {
        let dataSource = (source.indexOf('tbia') >=0 ) ? 'tbia' : source;
        let grid = new w2grid({
          name: 'grid1',
          box: '#grid1',
          header: 'Available Scientific Names',
          show: { header: true, footer: true },
            columns: [
              { field: 'key', text: 'taxonKey', size: '80px' },
              { field: 'scientificName', text: 'Scientific Name', size: '350px' },
              { field: 'status', text: 'Status', size: '80px' },
              { field: 'ref', text: 'Reference', size: '280px' },
              { field: 'accordingTo', text: 'According To', size: '180px' }
            ],
          url: sourceAPI,
          onClick(event) {
            const record = grid.get(event.detail.recid);
            let grid2 = new w2grid({
              name: 'grid2',
              box: '#grid2',
              header: 'Found Specimens',
              show: { header: true , footer: true},
              url: `/api/external/data/${dataSource}/${record.key}`,
              autoLoad: false,
              columns: [
                { field: 'basisOfRecord', text: 'Basis Of Record', size: '50px' },
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
              onClick(event) {
              },
            });
          },
        });
      }).close((e) => {
        if ('grid1' in w2ui) {
          w2ui['grid1'].destroy();
        }
        if ('grid2' in w2ui) {
          w2ui['grid2'].destroy();
        }
      }); // end of popup then
  }
})();
