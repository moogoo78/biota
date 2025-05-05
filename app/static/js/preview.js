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
})();
