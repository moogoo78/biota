 document.addEventListener('DOMContentLoaded', function () {
   const API_URL = '{{ API_URL }}';
   const itemData = {{ item_data_json|safe }};
   const TAICOL_REF_API = 'https://nametool.taicol.tw/api/citations';
   const CURRENT_URL = "{{ url_for('publication.detail_view', item_id=publication.id ) }}";
   let currentItemIndex = 0;
   let currentSpecimenIndex = 0;

   //console.log(itemData[0].fetched_specimens);
   const literatureSelect = new TomSelect('#literatures-select',{
     valueField: 'reference_id',
     labelField: 'citation',
     searchField: ['citation'],
     plugins:['virtual_scroll'],
     maxOptions: 200,

     // fetch remote data
     firstUrl: function(query){
       return `${TAICOL_REF_API}?keyword=` + encodeURIComponent(query);
     },
     load: function(query, callback) {
       const url = this.getUrl(query);
       fetch(url)
	 .then(response => response.json())
	 .then(json => {
	   //if( json.data.after ){
           if( parseInt(json.last_page) > parseInt(json.current_page) ){
	     const next_url = `${TAICOL_REF_API}?keyword=` + encodeURIComponent(query)+`&page=${parseInt(json.current_page) + 1}`;
	     this.setNextUrl(query, next_url);
	   }
	   //let data = json.data.children.map(row => row.data);
           console.log('citations results:', json);
	   callback(json.data);
	 }).catch((e)=>{
	   callback();
	 });
     },
     render: {
       loading_more: function(data, escape) {
	 return `<div class="loading-more-results py-2 d-flex align-items-center"><div class="spinner"></div> Loading more results </div>`;
       }
     },
   });

   const literatureAddButton = document.getElementById('literature-add-button');
   literatureAddButton.onclick = (e) => {
     e.preventDefault();
     const referenceId = literatureSelect.getValue();
     const citation = literatureSelect.getItem(referenceId).textContent;
     fetch(`${CURRENT_URL}/literatures/post`,{
       method: "POST",
       headers: {
         "Content-Type": "application/json",
       },
       body: JSON.stringify({
         reference_id: referenceId,
         citation: citation,
       }),
     })
       .then(resp => resp.json())
       .then(result => {
         //console.log(result);
         // force reload
         location.reload(true);
       });
   };


   function flashMessage(message) {
     const tpl = document.getElementById('toast-template');
     const msg = document.getElementById('toast-message');
     // show Toast manually (Because: Toast not defined?)
     tpl.classList.remove('hidden', 'opacity-0');
     tpl.classList.add('opacity-100');
     msg.textContent = message;
   }

   const specimenEditSubmit = document.getElementById('specimen-edit-submit');
   specimenEditSubmit.onclick = (e) => {
     e.preventDefault();
     const form = document.getElementById('specimen-edit-form');
     const formData = new FormData(form);
     let payload = {};
     if (!formData.get('county')) {
       alert('縣市為必填')
       return ;
     }
     for (const [k, v] of formData.entries()) {
       payload[k] = v;
     }
     payload.item_id = itemData[currentItemIndex].item_id;
     //payload['text'] = document.getElementById('specimen-edit-display').textContent;
     //console.log(payload);
     fetch(`${CURRENT_URL}/modify-specimen/patch`, {
       method: "POST",
       headers: {
         "Content-Type": "application/json",
       },
       body: JSON.stringify(payload),
     })
       .then(resp => resp.json())
       .then(result => {
         console.log(result);
         // update ItemData
         for (const [k, v] of Object.entries(payload)) {
           itemData[currentItemIndex].selected_specimens[currentSpecimenIndex][`_${k}`] = v;
         }
         //document.location.href = `${CURRENT_URL}#groups`;
         //document.querySelector('[data-modal-toggle="specimen-edit-modal"]').click();
         flashMessage('saved');
       });
   };

   // fetched specimen, update row status
   itemData.forEach( (item, index)  => {
     if (item.fetched_specimens.length > 0) {
       updateRowStatus(index, 'success', 'Complete', item.fetched_specimens.length);
     }
   });

   const imageButtons = document.querySelectorAll('.fetch-group-image-button');
   const imageButtons2 = document.querySelectorAll('.fetch-group-image-button2');
   const saveImageButtons = document.querySelectorAll('.save-group-image-button');
   saveImageButtons.forEach( x => {
     x.onclick = (e) => {
       e.preventDefault();
       const index = e.target.dataset.index;
       const itemId = itemData[index].item_id;
       const galleryForm = document.getElementById(`gallery-form-${index}`);
       const formData = new FormData(galleryForm);
       let payload = {};
       for (const pair of formData.entries()) {
         //console.log(pair[0], pair[1]);
         payload[pair[0]] = pair[1];
       }
       fetch(`/items/${itemId}/save-images?payload=${JSON.stringify(payload)}`)
         .then( resp => resp.json() )
         .then( result => {
           console.log(result);
         });
     };
   });
   imageButtons.forEach( x => {
     x.onclick = (e) => {
       e.preventDefault();
       const index = e.target.dataset.index;
       const name = itemData[index].name;
       const url = `https://api.inaturalist.org/v1/observations?taxon_name=${name}&photos=true&quality_grade=research&per_page=20`;

       console.log('fetch iNat:', url);
       fetch(url)
         .then(resp => resp.json())
         .then(data => {
           let photos = [];
           let resultsWrapper = document.getElementById(`group-gallery-${index}`);
           resultsWrapper.innerHTML = '';
           data.results.forEach( x => {
             photos = photos.concat(x.observation_photos);
           });
           console.log(photos.length, 'results');
           photos.forEach( x => {
             const box = document.createElement('div');
             const img = document.createElement('img');
             const input = document.createElement('input');
             const body = document.createElement('div');
             const flex = document.createElement('div');
             const label = document.createElement('label');
             box.classList.add('bg-white', 'border', 'border-gray-200', 'rounded-lg', 'shadow-sm', 'overflow-hidden');
             body.classList.add('p-4');
             img.classList.add('h-auto', 'max-w-full', 'rounded-lg');
             img.classList.add('w-full', 'h-48', 'object-cover');
             img.src = x.photo.url.replace('square', 'large');
             flex.classList.add('flex', 'items-center');
             input.dataset.identifier = x.id;
             input.type = 'checkbox';
             input.value = x.photo.url.replace('square', 'large') + '|' + x.photo.attribution;
             input.classList.add('w-4', 'h-4', 'border', 'border-gray-300', 'rounded-sm', 'text-blue-600', 'bg-gray-100', 'border-gray-300', 'rounded', 'focus:ring-3', 'focus:ring-blue-500');
             input.name = `chk-${x.id}`;
             label.classList.add('ms-2', 'text-xs', 'text-gray-600');
             label.textContent = x.photo.attribution;
             flex.appendChild(input);
             flex.appendChild(label);
             body.appendChild(flex);
             console.log(x.photo);
             box.appendChild(img);
             box.appendChild(body);
             resultsWrapper.appendChild(box);
           });
         })
     };
   });

   imageButtons2.forEach( x => {
     x.onclick = async (e) => {
       e.preventDefault();
       const index = e.target.dataset.index;
       const item = itemData[index];

       const nameSearchUrl = `${API_URL}/api/external/names/taicol/[${item.name_id}]${item.name}`;
       console.log(nameSearchUrl);
       const nameResponse = await fetch(nameSearchUrl);

       if (!nameResponse.ok) {
         throw new Error(`Name search failed: ${nameResponse.status}`);
       }

       const nameData = await nameResponse.json();


       // Use the first taxon key found
       const taxonKey = nameData.records[0].key;
       //console.log(taxonKey)
       const url = `${API_URL}/api/external/images/taieol/${taxonKey}`;
       console.log('fetch taieol:', url);
       fetch(url)
         .then(resp => resp.json())
         .then(data => {
           console.log('taieol: ', data);
           let photos = [];
           let resultsWrapper = document.getElementById(`group-gallery-${index}`);
           resultsWrapper.innerHTML = '';
           data.records.data.forEach( x => {
             x.associatedMedia.forEach( y => {
               photos = photos.concat(y.url);
             });
           });
           console.log(photos.length, 'results');
           photos.forEach( x => {
             const box = document.createElement('div');
             const img = document.createElement('img');
             const input = document.createElement('input');
             const body = document.createElement('div');
             const flex = document.createElement('div');
             const label = document.createElement('label');
             box.classList.add('bg-white', 'border', 'border-gray-200', 'rounded-lg', 'shadow-sm', 'overflow-hidden');
             body.classList.add('p-4');
             img.classList.add('h-auto', 'max-w-full', 'rounded-lg');
             img.classList.add('w-full', 'h-48', 'object-cover');
             img.src = x; //rl.replace('square', 'large');
             flex.classList.add('flex', 'items-center');
             input.dataset.identifier = '';//,x.id;
             input.type = 'checkbox';
             input.value = x;//x.photo.url.replace('square', 'large') + '|'; // + x.photo.attribution;
             input.classList.add('w-4', 'h-4', 'border', 'border-gray-300', 'rounded-sm', 'text-blue-600', 'bg-gray-100', 'border-gray-300', 'rounded', 'focus:ring-3', 'focus:ring-blue-500');
             input.name = `chk-${x}`;
             label.classList.add('ms-2', 'text-xs', 'text-gray-600');
             label.textContent = ''; //x.photo.attribution;
             flex.appendChild(input);
             flex.appendChild(label);
             body.appendChild(flex);
             console.log(x.photo);
             box.appendChild(img);
             box.appendChild(body);
             resultsWrapper.appendChild(box);
           });
         })
     };
   });

   /* sidebar and main panel */
   const sidebarNav = document.getElementById('sidebar-nav');
   const mainContent = document.getElementById('main-content');
   const sidebarItems = sidebarNav.querySelectorAll('.sidebar-item');
   const mainContentPanels = mainContent.querySelectorAll('.main-content-panel');
   const currentHash = window.location.hash;

   if (currentHash) {
     switchPanel(currentHash.substring(1));
   } else {
     switchPanel('preview');
   }
   function switchPanel(mainPanel) {
     //console.log(mainPanel);
     sidebarItems.forEach(item => {
       let icon = item.querySelector('svg');
       let label = item.querySelector('span');
       //let link = item.querySelector('a');
       icon.classList.remove('text-gray-900', 'text-gray-500');
       label.classList.remove('text-gray-900', 'text-gray-500');
       //link.classList.remove('text-gray-900', 'text-gray-500');
     });
     mainContentPanels.forEach(panel => {
       panel.classList.add('hidden');
     });
     const targetSidebarItem = sidebarNav.querySelector(`[data-main="${mainPanel}"]`);
     const targetPanel = document.getElementById(`main-content-${mainPanel}`);
     let icon = targetSidebarItem.querySelector('svg');
     let label = targetSidebarItem.querySelector('span');
     //let link = targetSidebarItem.querySelector('a');
     icon.classList.add('text-gray-900');
     label.classList.add('text-gray-900');
     //link.classList.add('text-gray-900');
     targetPanel.classList.remove('hidden');
     window.location.hash = mainPanel;
   }
   sidebarNav.onclick = (e) => {
     const clickedSidebar = event.target.closest('.sidebar-item');
     if (!clickedSidebar) return;
     e.preventDefault();
     const main = clickedSidebar.dataset.main;
     switchPanel(main);
   };

     /*
   const saveMetaButton = document.getElementById('save-meta-btn');
   saveMetaButton.onclick = (e) => {
     e.preventDefault();
     const form = document.getElementById('meta');
     const formData = new FormData(form);
     let params = new URLSearchParams();

     for (const [key, value] of formData) {
       params.set(key, value);
     }
     fetch(`${API_URL}/publications/patch?${params.toString()}`)
       .then(resp => resp.json())
       .then(result => {
           console.log(result);
           document.location.href = `${CURRENT_URL}#meta`;
       })
   };*/

       // Image modal functions
   window.showImageModal = function (imageUrl, collector, catalogNumber) {
     const modal = document.getElementById('image-modal');
     const img = document.getElementById('image-modal-img');
     const title = document.getElementById('image-modal-title');
     const info = document.getElementById('image-modal-info');
     
     img.src = imageUrl;
     title.textContent = `Specimen Image - ${catalogNumber || 'No catalog number'}`;
     info.innerHTML = `
       <p><strong>Collector:</strong> ${collector}</p>
       ${catalogNumber ? `<p><strong>Catalog Number:</strong> ${catalogNumber}</p>` : ''}
         <p class="mt-2"><a href="${imageUrl}" target="_blank" class="text-blue-600 hover:underline">View full resolution</a></p>
       `;
     
     modal.classList.remove('hidden');
     modal.classList.add('flex');
     
     // Close on background click
     modal.onclick = function(e) {
       if (e.target === modal) {
         closeImageModal();
       }
     };
   };

   window.closeImageModal = function() {
     const modal = document.getElementById('image-modal');
     modal.classList.add('hidden');
     modal.classList.remove('flex');
 };
   
   /* table row detail */
   document.getElementById('item-table-body').addEventListener('click', function(e) {
     const row = e.target.closest('.expandable-row');
     if (row) {
       // stop calling modal
       if (e.target.closest('.item-action')) {
         return;
       }
       const detailsRow = row.nextElementSibling;
       const chevron = row.querySelector('.chevron-icon');
       if (detailsRow) {
         detailsRow.classList.toggle('hidden');
         if (chevron) {
           chevron.classList.toggle('rotate-90');
         }
       }
     }
   });

   let deleteButton = document.getElementById('delete-button');
   deleteButton.onclick = (e) => {
     e.preventDefault();
     if (confirm('Are you sure?')) {
       document.location.href = "{{ url_for('publication.delete_item', item_id=publication.id ) }}";
     }
   };
   const getSpecimenBtn = document.getElementById('get-specimen-btn');
   getSpecimenBtn.onclick = (e) => {
     e.preventDefault();
     fetchAllTBIAData();
   }

   // Function to update row status
   function updateRowStatus(index, status, message, specimenCount = 0) {
     const row = document.querySelector(`tr[data-index="${index}"]`);
     if (!row) return;

     const statusDot = row.querySelector('.status-dot');
     const statusText = row.querySelector('.status-text');
     const spinner = row.querySelector('.spinner');
     const specimenCountDiv = row.querySelector('.specimen-count');
     const countSpan = row.querySelector('.count');
     const selectBtn = row.querySelector('.select-specimen-btn');
     const specimenEditBtn = row.querySelector('.specimen-edit-btn');

     // Hide spinner
     spinner.classList.add('hidden');

     // Update status
     switch(status) {
       case 'loading':
         statusDot.className = 'h-2.5 w-2.5 rounded-full bg-yellow-500 me-2 status-dot';
         statusText.textContent = message || 'Loading...';
         spinner.classList.remove('hidden');
         //specimenCountDiv.classList.add('hidden');
         selectBtn.classList.add('hidden');
         break;
       case 'success':
         statusDot.className = 'h-2.5 w-2.5 rounded-full bg-green-500 me-2 status-dot';
         statusText.textContent = 'Complete';
         countSpan.textContent = specimenCount;
         //specimenCountDiv.classList.remove('hidden');
         ;
         // Update the text based on whether this is showing found specimens or selected specimens
         /*
         const countText = specimenCountDiv.querySelector('.count').nextSibling;
         if (message && message.includes('selected')) {
           countText.textContent = ' selected';
         } else {
           countText.textContent = ' specimens found';
         }
         */
         if (specimenCount > 0) {
           //selectBtn.classList.remove('hidden');
           selectBtn.onclick = () => openSpecimenModal(index);
           specimenEditBtn.onclick = () => openSpecimenEditModal(index);
         }
         break;
       case 'error':
         statusDot.className = 'h-2.5 w-2.5 rounded-full bg-red-500 me-2 status-dot';
         statusText.textContent = message || 'Error';
         //specimenCountDiv.classList.add('hidden');
         selectBtn.classList.add('hidden');
         break;
       default:
         statusDot.className = 'h-2.5 w-2.5 rounded-full bg-gray-500 me-2 status-dot';
         statusText.textContent = message || 'Ready';
         //specimenCountDiv.classList.add('hidden');
         selectBtn.classList.add('hidden');
     }
   }

   // Function to fetch TBIA specimen data for a scientific name
   async function fetchTBIASpecimenData(scientificName, taicolNameId, index) {
     try {
       updateRowStatus(index, 'loading', 'Searching TBIA...');

       // First, search for the name to get taxon key
       const nameSearchUrl = `${API_URL}/api/external/names/taicol/[${taicolNameId}]${scientificName}`;
       const nameResponse = await fetch(nameSearchUrl);

       if (!nameResponse.ok) {
         throw new Error(`Name search failed: ${nameResponse.status}`);
       }

       const nameData = await nameResponse.json();

       if (nameData.status !== 'success' || !nameData.records || nameData.records.length === 0) {
         updateRowStatus(index, 'error', 'No TaiCOL records found');
         return;
       }

       // Use the first taxon key found
       const taxonKey = nameData.records[0].key;
       updateRowStatus(index, 'loading', 'Fetching specimens...');

       // Fetch specimen data using the taxon key
       const specimenUrl = `${API_URL}/api/external/data/tbia/${taxonKey}?item_id=${itemData[index].item_id}`;
       const specimenResponse = await fetch(specimenUrl);

       if (!specimenResponse.ok) {
         throw new Error(`Specimen search failed: ${specimenResponse.status}`);
       }

       const specimenData = await specimenResponse.json();

       if (specimenData.status === 'success') {
         const specimenCount = specimenData.records ? specimenData.records.length : 0;
         updateRowStatus(index, 'success', 'Complete', specimenCount);

         // Store the specimen data for later use
         //itemData[index].specimens = specimenData.records;
       } else {
         updateRowStatus(index, 'error', specimenData.message || 'No specimens found');
       }

     } catch (error) {
       console.error(`Error fetching data for ${scientificName}:`, error);
       updateRowStatus(index, 'error', error.message);
     }
   }

   // Function to process all scientific names
   async function fetchAllTBIAData () {
     if (itemData.length <= 0 ) {
       alert('No data available to process');
       return;
     }

     getSpecimenBtn.disabled = true;
     getSpecimenBtn.textContent = 'Processing...';

     const tbiaWrapper = document.getElementById('fetch-tbia-wrapper');
     const tbiaLabel = document.getElementById('fetch-tbia-label');
     const tbiaPa = document.getElementById('fetch-tbia-pa');
     const tbiaProgress = document.getElementById('fetch-tbia-progress');
     tbiaWrapper.classList.remove('hidden');
     try {
       // Process each scientific name one by one with a small delay
       for (let i = 0; i < itemData.length; i++) {
         const item = itemData[i];
         if (['34', '35', '36', '37', '38', '39', '40', '41', '42', '45', '46', '47'].includes(String(item.rank_id))) { // Only process 'species' rank (shlee)
           tbiaLabel.textContent = `fetching... [${item.name}] from TBIA`;
           let pa =  Math.round(((i+1) / itemData.length) * 100);
           tbiaPa.textContent = `${pa}%`;
           tbiaProgress.style = `width: ${pa}%`;
           await fetchTBIASpecimenData(item.name, item.name_id, i);

           // Add a small delay between requests to be respectful to the API
           if (i < itemData.length - 1) {
             await new Promise(resolve => setTimeout(resolve, 1000));
           }
         }
       }
     } finally {
       getSpecimenBtn.disabled = false;
       getSpecimenBtn.textContent = 'Get Specimen Data';
       console.log('get TBIA specimen data:', itemData);
       tbiaWrapper.classList.add('hidden');
       // Update publication status
       const data = await fetch(`${CURRENT_URL}/update-status/fetched`)
       const result = await data.json();
       //console.log(result);
       // refresh, let backend data display
       //location.reload();
       location.href = CURRENT_URL;
     };
   }
   function openSpecimenEditModal(index) {
     currentItemIndex = index;
     currentSpecimenIndex = 0;
     const item = itemData[index];
     if (item.selected_specimens.length === 0) {
       alert('no selected specimens')
       document.querySelector('[data-modal-toggle="specimen-edit-modal"]').click();
       return ;
     }
     if (item.selected_specimens.length > 0 && item.selected_specimens[0].associatedMedia) {
       imageDisplay.src = item.selected_specimens[0].associatedMedia;
     }
     document.getElementById('specimen-edit-modal-subtitle').textContent = item.name;
     refreshViewer(0);

   }

   function formatDate(dateString) {
     // Check if the input string has the correct format
     if (!/^\d{8}$/.test(dateString)) {
       return "Invalid date format. Please use 'YYYYMMDD'.";
     }

     // Extract year, month, and day using substring
     const year = dateString.substring(0, 4);
     const month = dateString.substring(4, 6);
     const day = dateString.substring(6, 8);

     // Return the new formatted string
     return `${year}-${month}-${day}`;
   }

   // Function to open specimen selection modal
   function openSpecimenModal(index) {
     currentItemIndex = index;
     const item = itemData[index];
     const fetched_specimens = itemData[index].fetched_specimens || [];
     let selectedIds = itemData[index].selected_specimens.map( x => x.id );

     // Update modal title
     document.getElementById('modal-species-name').textContent = item.name;

     // Populate counties dropdown based on available specimens
     populateCountiesDropdown(fetched_specimens);

     // Populate specimens table
     const tableBody = document.getElementById('specimens-table-body');
     tableBody.innerHTML = '';

     fetched_specimens.forEach((specimen, specimenIndex) => {
       const row = document.createElement('tr');
       row.className = 'bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600';
       const locality = specimen.locality ? specimen.locality.replace('|', ', ') : '';
       let date = '';
       if (specimen.eventDate) {
         date = formatDate(specimen.eventDate);
       }
       const collector = specimen.recordedBy || '';
       const catalogNumber = specimen.catalogNumber || '';
       const institutionCode = specimen.institutionCode || specimen.datasetTitle || '';
       
       // Get county information
       const county = getCountyFromSpecimen(specimen);
       const countyDisplay = county || 'Unknown';
       
       // Handle media/images
       const media = [specimen.associatedMedia, ] || [];
       const hasImage = media.length > 0;
       const firstImage = hasImage ? media : null;
       
       // Handle external URL
       const externalUrl = specimen.url || '';
       const hasUrl = externalUrl && externalUrl.trim() !== '';
       let checked = (selectedIds.indexOf(specimen.id) >= 0) ? " checked" : "";

       row.innerHTML = `
           <td class="px-3 py-2">
           <input type="checkbox" class="specimen-checkbox w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 dark:bg-gray-700 dark:border-gray-600" value="${specimenIndex}" data-county="${county}"${checked}>
           </td>
           <td class="px-3 py-2 text-center">
           ${hasImage ? `
       <div class="relative group">
       <img src="${firstImage}" alt="Specimen" class="w-12 h-12 object-cover rounded-lg border border-gray-200 cursor-pointer hover:shadow-md transition-shadow" onclick="showImageModal('${firstImage}', '${specimen.recordedBy || 'Unknown'}', '${catalogNumber}')">
       ${media.length > 1 ? `<span class="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">${media.length}</span>` : ''}
       </div>
       ` : `
       <div class="w-12 h-12 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center">
       <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
       <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
       </svg>
       </div>
       `}
           </td>
           <td class="px-3 py-2 text-xs">${institutionCode}</td>
           <td class="px-3 py-2 text-xs">${collector}</td>
           <td class="px-3 py-2 text-xs">${date}</td>
           <td class="px-3 py-2 text-xs max-w-xs truncate" title="${locality}">
           <span class="font-medium text-blue-600">${countyDisplay}</span><br>
           ${locality}
           </td>
           <td class="px-3 py-2 text-xs">${catalogNumber}</td>
           <td class="px-3 py-2 text-center">
             ${hasUrl ? `
       <a href="${externalUrl}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-blue-600 hover:text-blue-800 hover:underline">
       <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
       <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
       </svg>
       </a>
       ` : `
       <span class="text-gray-400">-</span>
       `}
           </td>
       `;
       
       tableBody.appendChild(row);
     });

     if (selectedIds.length >= 1) {
       document.querySelector('input[name="selection-method"][value="manual"]').checked = true;
     } else {
       // Reset selection method to auto
       document.querySelector('input[name="selection-method"][value="auto"]').checked = true;
     }
     updateSelectionMethod();
     // Clear previous selections
     updateSelectedSpecimensSummary();
   }

   // Function to update selection method visibility
   function updateSelectionMethod() {
     const isAuto = document.querySelector('input[name="selection-method"]:checked').value === 'auto';
     const autoCriteria = document.getElementById('auto-criteria');
     
     if (isAuto) {
       autoCriteria.style.display = 'block';
       // Auto-select specimens based on criteria
       autoSelectSpecimens();
     } else {
       autoCriteria.style.display = 'none';
     }
   }

   // Function to extract county from specimen data
   function getCountyFromSpecimen(specimen) {
     // Try different possible county sources
     if (specimen.named_areas && specimen.named_areas.adm2) {
       const chineseCounty = specimen.named_areas.adm2;
       return COUNTY_MAP[chineseCounty] ? COUNTY_MAP[chineseCounty].toUpperCase() : null;
     }
     
     // Try locality parsing
     if (specimen.locality) {
       const locality = specimen.locality.toLowerCase();
       for (const [chinese, english] of Object.entries(COUNTY_MAP)) {
         if (locality.includes(chinese) || locality.includes(english.toLowerCase())) {
           return english.toUpperCase();
         }
       }
     }
     
     return null;
   }

   // Function to populate counties dropdown
   function populateCountiesDropdown(specimens) {
     const targetCounties = document.getElementById('target-counties');
     targetCounties.innerHTML = '';
     
     // Get unique counties from specimens
     const availableCounties = new Set();
     specimens.forEach(specimen => {
       const county = getCountyFromSpecimen(specimen);
       if (county) {
         availableCounties.add(county);
       }
     });
     
     // Sort counties according to COUNTY_ORDER
     const sortedCounties = COUNTY_ORDER.filter(county => availableCounties.has(county));
     
     // Add options to dropdown
     sortedCounties.forEach(county => {
       const option = document.createElement('option');
       option.value = county;
       option.textContent = county;
       option.selected = true; // Select all by default
       targetCounties.appendChild(option);
     });
     
     // Add "Unknown" option if there are specimens without county info
     const unknownCount = specimens.filter(s => !getCountyFromSpecimen(s)).length;
     if (unknownCount > 0) {
       const option = document.createElement('option');
       option.value = 'UNKNOWN';
       option.textContent = `UNKNOWN (${unknownCount} specimens)`;
       targetCounties.appendChild(option);
     }
   }

   // Function to auto-select specimens based on county criteria
   function autoSelectSpecimens() {
     const maxSpecimens = parseInt(document.getElementById('max-specimens').value);
     const minPerCounty = parseInt(document.getElementById('min-specimens-per-county').value);
     const targetCounties = Array.from(document.getElementById('target-counties').selectedOptions)
                                 .map(option => option.value);
     const checkboxes = document.querySelectorAll('.specimen-checkbox');
     
     // Clear all selections first
     checkboxes.forEach(cb => cb.checked = false);
     
     // Group specimens by county
     const countyGroups = {};
     checkboxes.forEach(checkbox => {
       const county = checkbox.dataset.county || 'UNKNOWN';
       if (!countyGroups[county]) {
         countyGroups[county] = [];
       }
       countyGroups[county].push(checkbox);
     });
     
     let totalSelected = 0;
     
     // Select specimens for each target county
     for (const county of targetCounties) {
       if (totalSelected >= maxSpecimens) break;
       
       const specimens = countyGroups[county] || [];
       const toSelect = Math.min(minPerCounty, specimens.length, maxSpecimens - totalSelected);
       
       // Select the first N specimens from this county
       for (let i = 0; i < toSelect; i++) {
         specimens[i].checked = true;
         totalSelected++;
       }
     }
     
     updateSelectedSpecimensSummary();
   }

   // Function to update selected specimens summary
   function updateSelectedSpecimensSummary() {
     const selectedCheckboxes = document.querySelectorAll('.specimen-checkbox:checked');
     const summaryDiv = document.getElementById('selected-specimens-summary');
     
     if (selectedCheckboxes.length === 0) {
       summaryDiv.innerHTML = '<p>No specimens selected</p>';
     } else {
       const specimens = itemData[currentItemIndex].fetched_specimens;
       let summaryHTML = `<p><strong>${selectedCheckboxes.length} specimens selected:</strong></p><ul class="list-disc list-inside mt-2 space-y-1">`;
       
       selectedCheckboxes.forEach(checkbox => {
         const index = parseInt(checkbox.value);
         const specimen = specimens[index];
         const collector = specimen.recordedBy || 'Unknown collector';
         const date = specimen.date || 'No date';
         const locality = specimen.locality ? specimen.locality.replace('|', ', ').substring(0, 50) + '...' : 'Unknown locality';
         
         summaryHTML += `<li class="text-xs">${collector}, ${date} - ${locality}</li>`;
       });
       
       summaryHTML += '</ul>';
       summaryDiv.innerHTML = summaryHTML;
     }
   }

   // Function to save selected specimens
   function saveSelectedSpecimens() {
     const selectedCheckboxes = document.querySelectorAll('.specimen-checkbox:checked');
     const selectedIndices = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));

     //if (selectedIndices.length === 0) {
     //  alert('Please select at least one specimen');
     //  return;
     //}

     // Store selected specimens
     /*
     if (!itemData[currentSpecimenIndex].selectedSpecimens) {
       itemData[currentSpecimenIndex].selectedSpecimens = [];
     }

     itemData[currentSpecimenIndex].selectedSpecimens = selectedIndices.map(index => {
       return itemData[currentSpecimenIndex].fetched_specimens[index];
     });
     */

     //console.log('Selected specimens for', itemData[currentSpecimenIndex].name, selectedIndices);

     //let selectedIds = selectedIndices.map( x => {
     //  return itemData[currentSpecimenIndex].fetched_specimens[x]['_id'];
     //});
     // Patch ItemSpecimen
     fetch(`${CURRENT_URL}/items/${itemData[currentItemIndex]['item_id']}/patch-specimens?selected=${selectedIndices.join(',')}`)
       .then(data => data.json())
       .then(result => {
         console.log(result);
         location.reload();
       });

     // Update row status to show selection made
     //const selectedCount = selectedIndices.length;
     //updateRowStatus(currentSpecimenIndex, 'success', `${selectedCount} selected`, selectedCount);

     // Close modal
     //document.querySelector('[data-modal-toggle="specimen-modal"]').click(); // moogoo: this will ause currentSpecimenIndex reset to 0 !!   
   }

   // Event listeners
   document.addEventListener('change', function(e) {
     if (e.target.name === 'selection-method') {
       updateSelectionMethod();
     } else if (e.target.classList.contains('specimen-checkbox')) {
       updateSelectedSpecimensSummary();
     } else if (e.target.id === 'target-counties') {
       const isAuto = document.querySelector('input[name="selection-method"]:checked').value === 'auto';
       if (isAuto) {
         autoSelectSpecimens();
       }
     }
   });


   document.addEventListener('input', function(e) {
     if (e.target.id === 'max-specimens' || e.target.id === 'min-specimens-per-county') {
       const isAuto = document.querySelector('input[name="selection-method"]:checked').value === 'auto';
       if (isAuto) {
         autoSelectSpecimens();
       }
     }
   });

   document.getElementById('save-specimens-btn').addEventListener('click', saveSelectedSpecimens);

   /*
   document.getElementById('download-btn').addEventListener('click', (e) => {
     fetch(`${CURRENT_URL}/publish/post`,{
       method: "POST",
       headers: {
         "Content-Type": "application/json",
       },
       body: JSON.stringify({
         format: 'docx',
       }),
     })
       .then(resp => resp.json())
       .then(result => {
         console.log(result);
       });
       });
    */
   const literatureSaveButton = document.getElementById('literature-save-button');
   literatureSaveButton.onclick = (e) => {
     e.preventDefault();
     const form = document.getElementById('literature-form');
     const formData = new FormData(form);
     console.log(formData);
     let payload = {};
     for (const [key, value] of formData) {
       //console.log(key, value);
       let klist = key.split('_');
       payload[klist[1]] = value;
     }
     fetch(`${CURRENT_URL}/literatures/patch`, {
       method: "POST",
       headers: {
         "Content-Type": "application/json",
       },
       body: JSON.stringify(payload),
     })
       .then(resp => resp.json())
       .then(result => {
         console.log(result);
         //document.location.href = CURRENT_URL;
       });
   };

   {% include "_inc_image_viewer.js" %}
   const specimenEditModal = document.getElementById('specimen-edit-modal');
   let btnNext = document.getElementById('btn-viewer-next');
   let btnPrev = document.getElementById('btn-viewer-prev');
   function isFormElement(element) {
     const formTags = ['INPUT', 'TEXTAREA', 'SELECT'];
     return formTags.includes(element.tagName) ||
            element.contentEditable === 'true' ||
            element.isContentEditable;
   }
   const nextBtn = document.getElementById('specimen-edit-nav-next-btn');
   nextBtn.onclick = (e) => {
     if (currentSpecimenIndex < itemData[currentItemIndex].selected_specimens.length -1) {
       currentSpecimenIndex += 1;
       nextBtn.classList.remove('cursor-not-allowed');
       refreshViewer(currentSpecimenIndex);
     } else {
       nextBtn.classList.add('cursor-not-allowed');
     }
   };
   const prevBtn = document.getElementById('specimen-edit-nav-prev-btn');
   prevBtn.onclick = (e) => {
     if (currentSpecimenIndex > 0) {
       currentSpecimenIndex -= 1;
       prevBtn.classList.remove('cursor-not-allowed');
       refreshViewer(currentSpecimenIndex);
     } else {
       prevBtn.classList.add('cursor-not-allowed');
    }
   };

   function refreshViewer(idx) {
     let spData = itemData[currentItemIndex].selected_specimens[idx]
     //console.log(spData);
     if (spData.associatedMedia) {
       imageDisplay.src = spData.associatedMedia;
     }
     document.getElementById('specimen-edit-nav-index').textContent = idx + 1;
     document.getElementById('specimen-edit-nav-length').textContent = itemData[currentItemIndex].selected_specimens.length;
     document.getElementById('specimen-edit-spid').value = spData._id;
     const origRecordedBy = document.getElementById('specimen-edit-orig-recorded-by');
     const origRecordNumber = document.getElementById('specimen-edit-orig-record-number');
     const origCatalogNumber = document.getElementById('specimen-edit-orig-catalog-number');
     const origInstitutionCode = document.getElementById('specimen-edit-orig-institution-code');
     const origLocality = document.getElementById('specimen-edit-orig-locality');
     const origCounty = document.getElementById('specimen-edit-orig-county');
     const customRecordedBy = document.getElementById('specimen-edit-custom-recorded-by');
     const customRecordNumber = document.getElementById('specimen-edit-custom-record-number');
     const customLocality = document.getElementById('specimen-edit-custom-locality');
     const customInstitutionCode = document.getElementById('specimen-edit-custom-institution-code');
     const customCatalogNumber = document.getElementById('specimen-edit-custom-catalog-number');
     const customCounty = document.getElementById('specimen-edit-custom-county');
     const displayInput = document.getElementById('specimen-edit-display');
     const toItemSelect = document.getElementById('specimen-edit-to-item');

     /*
     const chk = document.getElementById('specimen-edit-custom-chk');
     chk.onchange = (e) => {
       isCustomSpecimenEdit = e.target.checked;
     };
     */
     const sort = document.getElementById('specimen-edit-sort');
     sort.value = spData._sort;

     origRecordedBy.textContent = spData.recordedBy;
     origRecordNumber.textContent = spData.recordNumber;
     origLocality.textContent = spData.locality;
     origCatalogNumber.textContent = spData.catalogNumber;
     origInstitutionCode.textContent = spData.institutionCode;
     customRecordedBy.value = spData._recorded_by;
     customRecordNumber.value = spData._record_number;
     customLocality.value = spData._locality;
     customCatalogNumber.value = spData._catalog_number;
     customInstitutionCode.value = spData._institution_code;
     displayInput.value = spData._text;

     customCounty[0] = new Option('-- choose --', '');
     COUNTY_ORDER.forEach( (county, idx) => {
       const foundEntry = Object.entries(COUNTY_MAP).find(([key, value]) => value.toUpperCase() === county);
       const foundKey = foundEntry ? foundEntry[0] : undefined;
       if (spData._county === county) {
         customCounty[idx+1] = new Option(foundKey, county, true, true);
       } else {
         customCounty[idx+1] = new Option(foundKey, county);
       }
     });
     customCounty[COUNTY_ORDER.length+1] = new Option('縣市不明', 'TBD');

     toItemSelect[0] = new Option('-- choose --', '');
     let counter = 0;
     itemData.forEach( x => {
       // species and below (subspecies, variety, form...): the same set the
       // TBIA fetch walks, so any of them can hold specimens
       if (x.rank_id >= 34) {
         counter += 1;
         toItemSelect[counter] = new Option(`${counter}. ${x.name}`, x.item_id);
       }
     });

     document.getElementById('specimen-edit-raw').innerHTML = JSON.stringify(spData, null, 2);

     function updateDisplay() {
       let recorded_by = customRecordedBy.value || '';
       let record_number = customRecordNumber.value || '';
       let catalog_number = customCatalogNumber.value || '';
       let institution_code = customInstitutionCode.value || '';
       let locality = customLocality.value || '';
       if (catalog_number) {
         displayInput.value = `${locality}, ${recorded_by} ${record_number} (${institution_code}[${catalog_number}])`;
       } else {
         displayInput.value = `${locality}, ${recorded_by} ${record_number} (${institution_code})`;
       }
     }

     /*
     let inputList = document.querySelectorAll('.specimen-edit-input');
     inputList.forEach ( x => {
       x.addEventListener('input', (event) => {
         if (!isCustomSpecimenEdit) {
           updateDisplay();
         }
       });
     });
     */
     //updateDisplay();
     const applyFormat = document.getElementById('specimen-edit-apply-format');
     applyFormat.onclick = (e) => {
       e.preventDefault();
       updateDisplay();
     }
   }

   document.addEventListener('keydown', function(event) {
     if (specimenEditModal.classList.contains("hidden")) {
       return;
     }
     if (isFormElement(document.activeElement)) {
       return; // Use default behavior for form elements
     }
     // Custom behavior for non-form elements
     if (event.keyCode == 39) {
       if (currentSpecimenIndex < itemData[currentItemIndex].selected_specimens.length -1) {
         currentSpecimenIndex += 1;
         nextBtn.classList.remove('cursor-not-allowed');
         refreshViewer(currentSpecimenIndex);
       } else {
         nextBtn.classList.add('cursor-not-allowed');
       }
     }
     else if (event.keyCode == 37) {
       if (currentSpecimenIndex > 0) {
         currentSpecimenIndex -= 1;
         prevBtn.classList.remove('cursor-not-allowed');
         refreshViewer(currentSpecimenIndex);
       } else {
         prevBtn.classList.add('cursor-not-allowed');
       }
     }
   });
   document.getElementById('specimen-edit-modal-close-btn').onclick = (e) => {
     const tpl = document.getElementById('toast-template');
     tpl.classList.add('hidden');
     console.log('close edit modal')
     document.location.reload();
   };

   document.getElementById('specimen-edit-new-btn').onclick = (e) => {
     imageDisplay.src = '';

     document.getElementById('specimen-edit-nav-index').textContent = 'new';
     document.getElementById('specimen-edit-nav-length').textContent = '-';
     document.getElementById('specimen-edit-spid').value = '';
     const origRecordedBy = document.getElementById('specimen-edit-orig-recorded-by');
     const origRecordNumber = document.getElementById('specimen-edit-orig-record-number');
     const origCatalogNumber = document.getElementById('specimen-edit-orig-catalog-number');
     const origInstitutionCode = document.getElementById('specimen-edit-orig-institution-code');
     const origLocality = document.getElementById('specimen-edit-orig-locality');
     const origCounty = document.getElementById('specimen-edit-orig-county');
     const customRecordedBy = document.getElementById('specimen-edit-custom-recorded-by');
     const customRecordNumber = document.getElementById('specimen-edit-custom-record-number');
     const customLocality = document.getElementById('specimen-edit-custom-locality');
     const customInstitutionCode = document.getElementById('specimen-edit-custom-institution-code');
     const customCatalogNumber = document.getElementById('specimen-edit-custom-catalog-number');
     const customCounty = document.getElementById('specimen-edit-custom-county');
     const displayInput = document.getElementById('specimen-edit-display');

     const sort = document.getElementById('specimen-edit-sort');
     sort.value = '';

     origRecordedBy.textContent = '';
     origRecordNumber.textContent = '';
     origLocality.textContent = '';
     origCatalogNumber.textContent = '';
     origInstitutionCode.textContent = '';
     customRecordedBy.value = '';
     customRecordNumber.value = '';
     customLocality.value = '';
     customCatalogNumber.value = '';
     customInstitutionCode.value = '';
     displayInput.value = '';

     customCounty[0] = new Option('-- choose --', '');
     COUNTY_ORDER.forEach( (county, idx) => {
       const foundEntry = Object.entries(COUNTY_MAP).find(([key, value]) => value.toUpperCase() === county);
       const foundKey = foundEntry ? foundEntry[0] : undefined;
       customCounty[idx+1] = new Option(foundKey, county);
     });
     customCounty[COUNTY_ORDER.length+1] = new Option('縣市不明', 'TBD');

     document.getElementById('specimen-edit-raw').innerHTML = '';
   };

   const urlParams = new URLSearchParams(window.location.search);
   const action = urlParams.get('action');
   if (action && action === 'fetchAll') {
     //location.href = `${CURRENT_URL}#group`;
     fetchAllTBIAData();
   }
 });
