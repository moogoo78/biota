(function() {
  'use strict';

   const getSpecimenBtn = document.getElementById('get-specimen-btn');
   const selectSpecimensBtn = document.getElementById('select-specimens-btn');
   const previewOutputBtn = document.getElementById('preview-output-btn');
   const namespaceTable = document.getElementById('namespace-table');
   const previewLayout = document.getElementById('preview-layout');

   const sidebarNav = document.getElementById('sidebar-nav');
   const mainContent = document.getElementById('main-content');

   const sidebarItems = sidebarNav.querySelectorAll('.sidebar-item');
   const mainContentPanels = mainContent.querySelectorAll('.main-content-panel');

   function switchPanel(mainPanel) {
     sidebarItems.forEach(item => {
       let icon = item.querySelector('svg');
       let label = item.querySelector('span');
       icon.classList.remove('text-gray-900', 'text-gray-500');
       label.classList.remove('text-gray-900', 'text-gray-500');
     });

     mainContentPanels.forEach(panel => {
       panel.classList.add('hidden');
     });

     const targetSidebarItem = sidebarNav.querySelector(`[data-main="${mainPanel}"]`);
     const targetPanel = document.getElementById(`main-content-${mainPanel}`);
     let icon = targetSidebarItem.querySelector('svg');
     let label = targetSidebarItem.querySelector('span');
     icon.classList.add('text-gray-900');
     label.classList.add('text-gray-900');
     targetPanel.classList.remove('hidden');

   }
   sidebarNav.onclick = (e) => {
     const clickedSidebar = event.target.closest('.sidebar-item');
     if (!clickedSidebar) return;
     e.preventDefault();
     const main = clickedSidebar.dataset.main;
     switchPanel(main);
   }

   
   let namespaceId;
   let namespacePart = {};
     let isLoading = true;
     let error = null;
     let stepKey = 1;
     let speciesInfo = [];
     let infoState = [];
     let currentSpecimenIndex = -1;

     // Stepper management
     function updateStepper(step) {
       const step1Indicator = document.getElementById('step1-indicator');
       const step2Indicator = document.getElementById('step2-indicator');
       const step3Indicator = document.getElementById('step3-indicator');
       const progressBar1 = document.getElementById('progress-bar-1');
       const progressBar2 = document.getElementById('progress-bar-2');
       //const selectSpecimensBtn = document.getElementById('select-specimens-btn');
       //const previewOutputBtn = document.getElementById('preview-output-btn');
       
       if (step === 1) {
         // Step 1 active
         step1Indicator.className = 'flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full lg:h-12 lg:w-12 dark:bg-blue-800 shrink-0';
         step2Indicator.className = 'flex items-center justify-center w-10 h-10 bg-gray-100 rounded-full lg:h-12 lg:w-12 dark:bg-gray-800 shrink-0';
         step3Indicator.className = 'flex items-center justify-center w-10 h-10 bg-gray-100 rounded-full lg:h-12 lg:w-12 dark:bg-gray-800 shrink-0';
         progressBar1.style.width = '0%';
         progressBar2.style.width = '0%';
       } else if (step === 2) {
         // Step 2 active
         step1Indicator.className = 'flex items-center justify-center w-10 h-10 bg-green-100 rounded-full lg:h-12 lg:w-12 dark:bg-green-800 shrink-0';
         step2Indicator.className = 'flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full lg:h-12 lg:w-12 dark:bg-blue-800 shrink-0';
         step3Indicator.className = 'flex items-center justify-center w-10 h-10 bg-gray-100 rounded-full lg:h-12 lg:w-12 dark:bg-gray-800 shrink-0';
         progressBar1.style.width = '100%';
         progressBar2.style.width = '0%';
         selectSpecimensBtn.disabled = false;
         selectSpecimensBtn.className = 'text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800';
       } else if (step === 3) {
         // Step 3 active
         step1Indicator.className = 'flex items-center justify-center w-10 h-10 bg-green-100 rounded-full lg:h-12 lg:w-12 dark:bg-green-800 shrink-0';
         step2Indicator.className = 'flex items-center justify-center w-10 h-10 bg-green-100 rounded-full lg:h-12 lg:w-12 dark:bg-green-800 shrink-0';
         step3Indicator.className = 'flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full lg:h-12 lg:w-12 dark:bg-blue-800 shrink-0';
         progressBar1.style.width = '100%';
         progressBar2.style.width = '100%';
         previewOutputBtn.disabled = false;
         previewOutputBtn.className = 'text-white bg-green-700 hover:bg-green-800 focus:ring-4 focus:ring-green-300 font-medium rounded-lg text-sm px-5 py-2.5 dark:bg-green-600 dark:hover:bg-green-700 focus:outline-none dark:focus:ring-green-800';
         document.getElementById('output-preview-section').classList.remove('hidden');
         
         // Collapse the table when entering Step 3
         collapseTable();
         
         generateOutputPreview();
       }
       stepKey = step;

       // Only disable Step 3 button if no specimens are selected
       enableStep3ButtonIfReady();
     }

     function render ( data ) {
       document.getElementById('init-literatures').innerHTML = generateLiteratures(data.literatures);

       const itemTableBody = document.getElementById('item-table-body');
       itemTableBody.innerHTML = '';
       data.items.forEach( (item, index) => {
         const template = document.getElementById('item-row-template');
         const clone = template.content.cloneNode(true);
         const mainRow = clone.children[0];
         const detailsRow = clone.children[1];

         let scientificNameEl = mainRow.querySelector('.item-scientific-name');
         let scientificNameAuthorsEl = mainRow.querySelector('.item-scientific-name-authors');
         let commonNameEl = mainRow.querySelector('.item-common-name');

         // Set row id for later reference
         mainRow.setAttribute('data-index', index);
         mainRow.setAttribute('data-scientific-name', item.item_title.scientific_name.canonical);

         scientificNameEl.textContent = item.item_title.scientific_name.canonical;
         scientificNameAuthorsEl.innerHTML = `&nbsp;${item.item_title.scientific_name.author}` || '';
         commonNameEl.textContent = item.commonNames.join(', ');

         let updatedEl = mainRow.querySelector('.item-updated');
         updatedEl.textContent = item.updated;

         // Populate details row
         const detailsContainer = detailsRow.querySelector('.details-container');
         detailsContainer.querySelector('.item-scientific-name').textContent = item.item_title.scientific_name.canonical;


         const p1 = document.createElement('p');
         const bold1 = document.createElement('b');
         bold1.textContent = '[name_remark]';
         detailsContainer.appendChild(bold1);
         p1.textContent = item.item_title?.name_remark || '--';
         detailsContainer.appendChild(p1);

         const hrCls = 'inline-flex items-center justify-center w-full'.split(' ');

         if (item.synonyms.length) {
           const b = document.createElement('b');
           b.textContent = 'Synonyms';
           detailsContainer.appendChild(b);

           item.synonyms.forEach( x => {
             const p = document.createElement('p');
             const s = document.createElement('span');
             const i = document.createElement('i');
             i.textContent = x.name;
             p.appendChild(i);
             s.textContent = ` ${x.formatted_authors}`;
             if (x.properties?.indications.length) {
               s.textContent = ` ${s.textContent} ${x.properties?.indications.join(' ')}`;
             }
             p.appendChild(s);
             detailsContainer.appendChild(p);
           });
         }

         const p2 = document.createElement('p');
         const bold2 = document.createElement('b');
         bold2.textContent = 'Note';
         detailsContainer.appendChild(bold2);
         p2.textContent = item.properties.note || '';
         detailsContainer.appendChild(p2);

         item.properties.additional_fields.forEach( aField => {
           const p = document.createElement('p');
           const bold = document.createElement('b');
           bold.textContent = String(aField.field_name).charAt(0).toUpperCase() + String(aField.field_name).slice(1);
           p.textContent = aField.field_value;
           detailsContainer.appendChild(bold);
           detailsContainer.appendChild(p);
         });
         // seperator
         const hrDiv = document.createElement('div');
         hrDiv.classList.add(...hrCls);
         hrDiv.innerHTML = '<hr class="w-64 h-px my-8 bg-gray-200 border-0 dark:bg-gray-700"><span class="absolute px-3 font-medium text-gray-900 -translate-x-1/2 bg-white left-1/2 dark:text-white dark:bg-gray-900">custom</span></div>';
         detailsContainer.appendChild(hrDiv);

         item.properties.custom_fields.forEach( aField => {
           const p = document.createElement('p');
           const bold = document.createElement('b');
           bold.textContent = String(aField.field_name_en).charAt(0).toUpperCase() + String(aField.field_name_en).slice(1) + ' / ' + aField.field_name_zh;
           p.textContent = aField.field_value;
           detailsContainer.appendChild(bold);
           detailsContainer.appendChild(p);
         });

         // seperator
         const hrDiv2 = document.createElement('div');
         hrDiv2.classList.add(...hrCls);
         hrDiv2.innerHTML = '<hr class="w-64 h-px my-8 bg-gray-200 border-0 dark:bg-gray-700"><span class="absolute px-3 font-medium text-gray-900 -translate-x-1/2 bg-white left-1/2 dark:text-white dark:bg-gray-900">Type Specimens</span></div>';
         detailsContainer.appendChild(hrDiv2);

         const pre = document.createElement('pre');
         pre.textContent = `${JSON.stringify(item.type_specimens, null, 2)}`;
         detailsContainer.appendChild(pre);

         itemTableBody.appendChild(clone);
       });
       initFlowbite();
     }

     async function init() {
       const urlParams = new URLSearchParams(window.location.search);
       namespaceId = urlParams.get('namespace_id');

       if (!namespaceId) {
         error = "namespace_id not found in URL";
         isLoading = false;
         render();
         return;
       }

       try {
         const response = await fetch(`${API_URL}/api/namespaces/${namespaceId}`);
         if (!response.ok) {
           throw new Error(`HTTP error! status: ${response.status}`);
         }
         let data = await response.json();
         namespacePart = data[0]; // get first
         console.log('get_namespace', data[0]);
         namespacePart.items.forEach(x => {
           speciesInfo.push({
             recid: x.taicol_usage_id,
             selectedIds: [],
             distributions: [],
             specimens: [],
             specimenData: [],
           });
           infoState.push({
             progress: 'init',
             loading: false,
           });
         });
       } catch (e) {
         error = e.message;
       } finally {
         isLoading = false;
         render(namespacePart);
       }
     } // end of init

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

       // Hide spinner
       spinner.classList.add('hidden');

       // Update status
       switch(status) {
         case 'loading':
           statusDot.className = 'h-2.5 w-2.5 rounded-full bg-yellow-500 me-2 status-dot';
           statusText.textContent = message || 'Loading...';
           spinner.classList.remove('hidden');
           specimenCountDiv.classList.add('hidden');
           selectBtn.classList.add('hidden');
           break;
         case 'success':
           statusDot.className = 'h-2.5 w-2.5 rounded-full bg-green-500 me-2 status-dot';
           statusText.textContent = 'Complete';
           countSpan.textContent = specimenCount;
           specimenCountDiv.classList.remove('hidden');
;
           // Update the text based on whether this is showing found specimens or selected specimens
           const countText = specimenCountDiv.querySelector('.count').nextSibling;
           if (message && message.includes('selected')) {
             countText.textContent = ' selected';
           } else {
             countText.textContent = ' specimens found';
           }
           if (specimenCount > 0) {
             selectBtn.classList.remove('hidden');
             selectBtn.onclick = () => openSpecimenModal(index);
           }
           break;
         case 'error':
           statusDot.className = 'h-2.5 w-2.5 rounded-full bg-red-500 me-2 status-dot';
           statusText.textContent = message || 'Error';
           specimenCountDiv.classList.add('hidden');
           selectBtn.classList.add('hidden');
           break;
         default:
           statusDot.className = 'h-2.5 w-2.5 rounded-full bg-gray-500 me-2 status-dot';
           statusText.textContent = message || 'Ready';
           specimenCountDiv.classList.add('hidden');
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
         const specimenUrl = `${API_URL}/api/external/data/tbia/${taxonKey}`;
         const specimenResponse = await fetch(specimenUrl);

         if (!specimenResponse.ok) {
           throw new Error(`Specimen search failed: ${specimenResponse.status}`);
         }

         const specimenData = await specimenResponse.json();

         if (specimenData.status === 'success') {
           const specimenCount = specimenData.records ? specimenData.records.length : 0;
           updateRowStatus(index, 'success', 'Complete', specimenCount);

           // Store the specimen data for later use
           speciesInfo[index].specimenData = specimenData.records;
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
       if (!namespacePart || !namespacePart.items) {
         alert('No data available to process');
         return;
       }

       const button = document.getElementById('get-specimen-btn');
       button.disabled = true;
       button.textContent = 'Processing...';

       try {
         // Process each scientific name one by one with a small delay
         for (let i = 0; i < namespacePart.items.length; i++) {
           const item = namespacePart.items[i];
           const scientificName = item.item_title.scientific_name.canonical;
           await fetchTBIASpecimenData(scientificName, item.taicol_taxon_name_id, i);

           // Add a small delay between requests to be respectful to the API
           if (i < namespacePart.items.length - 1) {
             await new Promise(resolve => setTimeout(resolve, 1000));
           }
         }
       } finally {
         button.disabled = false;
         button.textContent = 'Step 1: Get Specimen Data';
         console.log('after step1', speciesInfo);

         // Check if any specimens were found and move to step 2
         const hasSpecimens = speciesInfo.some(info => info.specimenData && info.specimenData.length > 0);
         if (hasSpecimens) {
           updateStepper(2);
         }
       }
     }

     // Function to open specimen selection modal
     function openSpecimenModal(index) {
       currentSpecimenIndex = index;
       const item = namespacePart.items[index];
       const specimens = speciesInfo[index].specimenData || [];
       
       // Update modal title
       document.getElementById('modal-species-name').textContent = item.item_title.scientific_name.canonical;
       
       // Populate counties dropdown based on available specimens
       populateCountiesDropdown(specimens);
       
       // Populate specimens table
       const tableBody = document.getElementById('specimens-table-body');
       tableBody.innerHTML = '';
       
       specimens.forEach((specimen, specimenIndex) => {
         const row = document.createElement('tr');
         row.className = 'bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600';
         
         const locality = specimen.locality ? specimen.locality.replace('|', ', ') : '';
         const date = specimen.date || '';
         const collector = specimen.recordedBy || '';
         const catalogNumber = specimen.catalogNumber || '';
         const institutionCode = specimen.institutionCode || specimen.datasetTitle || '';
         
         // Get county information
         const county = getCountyFromSpecimen(specimen);
         const countyDisplay = county || 'Unknown';
         
         // Handle media/images
         const media = specimen.media || [];
         const hasImage = media.length > 0;
         const firstImage = hasImage ? media[0] : null;
         
         // Handle external URL
         const externalUrl = specimen.url || '';
         const hasUrl = externalUrl && externalUrl.trim() !== '';
         
         row.innerHTML = `
           <td class="px-3 py-2">
             <input type="checkbox" class="specimen-checkbox w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 dark:bg-gray-700 dark:border-gray-600" value="${specimenIndex}" data-county="${county}">
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
       
       // Reset selection method to auto
       document.querySelector('input[name="selection-method"][value="auto"]').checked = true;
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
         const specimens = speciesInfo[currentSpecimenIndex].specimenData;
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
       
       if (selectedIndices.length === 0) {
         alert('Please select at least one specimen');
         return;
       }
       // Store selected specimens
       if (!speciesInfo[currentSpecimenIndex].selectedSpecimens) {
         speciesInfo[currentSpecimenIndex].selectedSpecimens = [];
       }
       
       speciesInfo[currentSpecimenIndex].selectedSpecimens = selectedIndices.map(index => {
         return speciesInfo[currentSpecimenIndex].specimenData[index];
       });
       
       console.log('Selected specimens for', namespacePart.items[currentSpecimenIndex].item_title.scientific_name.canonical, selectedIndices);

      
       // Update row status to show selection made
       const selectedCount = selectedIndices.length;
       updateRowStatus(currentSpecimenIndex, 'success', `${selectedCount} selected`, selectedCount);

       // Close modal
       document.querySelector('[data-modal-toggle="specimen-modal"]').click(); // moogoo: this will cause currentSpecimenIndex reset to 0 !! 
       
       // Enable Step 3 button but don't automatically move to Step 3
       enableStep3ButtonIfReady();
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

     // Image modal functions
     window.showImageModal = function(imageUrl, collector, catalogNumber) {
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

     // Close modal on escape key
     document.addEventListener('keydown', function(e) {
       if (e.key === 'Escape') {
         const imageModal = document.getElementById('image-modal');
         if (!imageModal.classList.contains('hidden')) {
           closeImageModal();
         }
       }
     });

     // Step 3 Functions
     function enableStep3ButtonIfReady() {
       // Check if any species has selected specimens
       const hasSelections = speciesInfo.some(info => 
         info.selectedSpecimens && info.selectedSpecimens.length > 0
       );
       
       const previewOutputBtn = document.getElementById('preview-output-btn');
       if (previewOutputBtn) {
         if (hasSelections) {
           // Enable the Step 3 button but don't automatically move to Step 3
           previewOutputBtn.disabled = false;
           previewOutputBtn.className = 'text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800';
         } else {
           // Disable the Step 3 button when no selections
           previewOutputBtn.disabled = true;
           previewOutputBtn.className = 'text-gray-400 bg-gray-200 cursor-not-allowed font-medium rounded-lg text-sm px-5 py-2.5 dark:bg-gray-700 dark:text-gray-500';
         }
       }
     }

     function generateOutputPreview() {
       const selectedData = [];
       const countySet = new Set();
       let totalSpecimens = 0;
       let speciesWithImages = 0;
       
       // Collect data for species with selected specimens
       for (let i = 0; i < namespacePart.items.length; i++) {
         const item = namespacePart.items[i];
         const selectedSpecimens = speciesInfo[i].selectedSpecimens;
         
         if (selectedSpecimens && selectedSpecimens.length > 0) {
           totalSpecimens += selectedSpecimens.length;
           
           // Check if any specimen has images
           const hasImages = selectedSpecimens.some(spec => spec.media && spec.media.length > 0);
           if (hasImages) speciesWithImages++;
           
           // Collect counties
           selectedSpecimens.forEach(spec => {
             const county = getCountyFromSpecimen(spec);
             if (county) countySet.add(county);
           });
           
           selectedData.push({
             species: item.item_title.scientific_name.canonical,
             commonNames: item.commonNames || [],
             specimens: selectedSpecimens,
             speciesIndex: i
           });
         }
       }
       
       // Update statistics
       document.getElementById('stats-species').textContent = selectedData.length;
       document.getElementById('stats-specimens').textContent = totalSpecimens;
       document.getElementById('stats-counties').textContent = countySet.size;
       document.getElementById('stats-images').textContent = speciesWithImages;
       
       // Generate formatted output
       generateFormattedOutput(selectedData);
       
       // Generate JSON output
       generateJSONOutput(selectedData);
       
       // Generate preview layout
       generatePreviewLayout(selectedData);
     }

     function generateFormattedOutput(selectedData) {
       const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
       let output = `Biota Specimen Selection Report\n`;
       output += `Generated: ${new Date().toISOString()}\n`;
       output += `Filename: ${timestamp}.txt\n\n`;
       output += `Summary:\n`;
       output += `- ${selectedData.length} species\n`;
       output += `- ${selectedData.reduce((sum, sp) => sum + sp.specimens.length, 0)} specimens\n`;
       output += `- ${new Set(selectedData.flatMap(sp => sp.specimens.map(spec => getCountyFromSpecimen(spec)).filter(c => c))).size} counties\n\n`;
       
       output += `SPECIMENS BY SPECIES:\n`;
       output += `${'='.repeat(50)}\n\n`;
       
       selectedData.forEach((species, index) => {
         output += `${index + 1}. ${species.species}\n`;
         if (species.commonNames.length > 0) {
           output += `   Common names: ${species.commonNames.join(', ')}\n`;
         }
         output += `   Selected specimens (${species.specimens.length}):\n\n`;
         
         species.specimens.forEach((specimen, specIndex) => {
           const county = getCountyFromSpecimen(specimen) || 'Unknown';
           const collector = specimen.recordedBy || 'Unknown collector';
           const date = specimen.date || 'No date';
           const catalogNumber = specimen.catalogNumber || 'No catalog number';
           const locality = specimen.locality ? specimen.locality.replace('|', ', ') : 'Unknown locality';
           const hasImages = specimen.media && specimen.media.length > 0;
           
           output += `   ${specIndex + 1}. ${collector} ${catalogNumber} (${date})\n`;
           output += `      County: ${county}\n`;
           output += `      Locality: ${locality}\n`;
           if (hasImages) {
             output += `      Images: ${specimen.media.length}\n`;
           }
           if (specimen.url) {
             output += `      URL: ${specimen.url}\n`;
           }
           output += `\n`;
         });
         
         output += `\n`;
       });
       
       document.getElementById('formatted-output').textContent = output;
     }

     function generateJSONOutput(selectedData) {
       const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
       
       const jsonData = {
         metadata: {
           generated: new Date().toISOString(),
           filename: `${timestamp}.json`,
           summary: {
             species_count: selectedData.length,
             specimen_count: selectedData.reduce((sum, sp) => sum + sp.specimens.length, 0),
             county_count: new Set(selectedData.flatMap(sp => sp.specimens.map(spec => getCountyFromSpecimen(spec)).filter(c => c))).size,
             species_with_images: selectedData.filter(sp => sp.specimens.some(spec => spec.media && spec.media.length > 0)).length
           }
         },
         namespace: {
           id: namespaceId,
           title: namespacePart.title || '',
           author: namespacePart.author || ''
         },
         species: selectedData.map(species => ({
           scientific_name: species.species,
           common_names: species.commonNames,
           selected_specimens: species.specimens.map(specimen => ({
             collector: specimen.recordedBy || null,
             catalog_number: specimen.catalogNumber || null,
             collection_date: specimen.date || null,
             county: getCountyFromSpecimen(specimen) || null,
             locality: specimen.locality || null,
             institution: specimen.institutionCode || specimen.datasetTitle || null,
             media: specimen.media || [],
             url: specimen.url || null,
             named_areas: specimen.named_areas || {},
             specimen_display: specimen.specimen_display || {}
           }))
         }))
       };
       
       document.getElementById('json-output').textContent = JSON.stringify(jsonData, null, 2);
     }

     function generateLiteratures(data=[]){
       let html = '';
       if ( data.length > 0) {
         html += `
           <h2 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">LITERATURES</h2>
           <ul class="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400 mb-6">
         `;
         data.forEach(lit => {
           html += `<li>${lit.content || lit.title || lit.author}</li>`;
         });
         html += '</ul>';
       }
       return html;
     }

     function generatePreviewLayout(selectedData) {
       const previewLayout = document.getElementById('preview-layout');
       if (!previewLayout) return;
       
       // Clear existing content
       previewLayout.innerHTML = '';
       
       // Generate title and author with inline editing
       const title = namespacePart.title || 'Taxonomic Specimen Report';
       const author = namespacePart.author || 'Unknown Author';
       
       let html = `
         <div class="mb-6 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
           <div class="flex items-center justify-between mb-4">
             <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Document Information</h3>
             <button id="edit-info-btn" onclick="toggleEditMode()" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
               <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
               </svg>
             </button>
           </div>
           
           <!-- Display Mode -->
           <div id="display-mode">
             <h1 class="mb-2 text-2xl font-bold text-gray-900 dark:text-white" id="display-title">${title}</h1>
             <p class="mb-4 text-lg text-gray-700 dark:text-gray-300">Author: <span id="display-author">${author}</span></p>
           </div>
           
           <!-- Edit Mode (hidden by default) -->
           <div id="edit-mode" class="hidden">
             <div class="mb-4">
               <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Title:</label>
               <input type="text" id="edit-title-input" value="${title}" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white">
             </div>
             <div class="mb-4">
               <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Author:</label>
               <input type="text" id="edit-author-input" value="${author}" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white">
             </div>
             <div class="flex space-x-2">
               <button id="save-info-btn" onclick="saveDocumentInfo()" class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md text-sm">
                 Save Changes
               </button>
               <button onclick="cancelEditMode()" class="bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-md text-sm">
                 Cancel
               </button>
               <button id="next-step-btn" onclick="goToFinalStep()" class="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md text-sm ml-auto">
                 Next Step →
               </button>
             </div>
           </div>
         </div>
         
         <!-- Document Content -->
         <div id="document-content">
       `;

       html += generateLiteratures(namespacePart.literatures);

       // Generate species entries with selected specimens
       selectedData.forEach((species, index) => {
         const item = namespacePart.items[species.speciesIndex];
         const scientificName = species.species;
         const commonNames = species.commonNames.join(', ');
         
         // Create specimen citation format
         let specimenCitations = [];
         species.specimens.forEach(specimen => {
           const county = getCountyFromSpecimen(specimen);
           const locality = specimen.locality ? specimen.locality.replace('|', ', ') : '';
           const collector = specimen.recordedBy || '';
           const date = specimen.date || '';
           const catalogNumber = specimen.catalogNumber || '';
           const institutionCode = specimen.institutionCode || specimen.datasetTitle || '';
           
           let citation = '';
           if (county) citation += `${county.toUpperCase()}: `;
           if (locality) citation += `${locality}, `;
           if (collector) citation += `${collector} `;
           if (catalogNumber) citation += `${catalogNumber}`;
           if (date) citation += ` (${date})`;
           if (institutionCode) citation += ` [${institutionCode}]`;
           
           specimenCitations.push(citation);
         });
         
         // Build the species entry
         html += `
           <div class="mb-8 border-b border-gray-200 dark:border-gray-700 pb-6">
             <h4 class="font-bold text-gray-900 dark:text-white text-xl mb-2">
               ${index + 1}. <em>${scientificName}</em>
             </h4>
             ${commonNames ? `<p class="text-gray-700 dark:text-gray-300 text-lg mb-3">${commonNames}</p>` : ''}
             
             ${item.addFields && item.addFields.description ? `
               <div class="mb-4">
                 <h5 class="font-semibold text-gray-900 dark:text-white mb-2">DESCRIPTION</h5>
                 <p class="text-gray-800 dark:text-gray-200 text-sm leading-relaxed">${item.addFields.description}</p>
               </div>
             ` : ''}
             
             ${species.specimens.length > 0 ? `
               <div class="mb-4">
                 <h5 class="font-semibold text-gray-900 dark:text-white mb-2">SPECIMENS EXAMINED (${species.specimens.length})</h5>
                 <div class="text-gray-800 dark:text-gray-200 text-sm leading-relaxed">
                   ${specimenCitations.map(citation => `<p class="mb-1">${citation}</p>`).join('')}
                 </div>
               </div>
             ` : ''}
             
             ${item.synonyms && item.synonyms.length > 0 ? `
               <div class="mb-4">
                 <h5 class="font-semibold text-gray-900 dark:text-white mb-2">SYNONYMS</h5>
                 <ul class="text-gray-600 dark:text-gray-400 text-sm">
                   ${item.synonyms.map(syn => `<li><em>${syn[0]}</em>${syn[1] ? ` [${syn[1]}]` : ''}</li>`).join('')}
                 </ul>
               </div>
             ` : ''}
             
             <div class="mt-3 text-xs text-gray-500 dark:text-gray-400">
               <span class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded mr-2">
                 ${species.specimens.length} specimens
               </span>
               ${new Set(species.specimens.map(s => getCountyFromSpecimen(s)).filter(c => c)).size > 0 ? `
                 <span class="inline-block bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded mr-2">
                   ${new Set(species.specimens.map(s => getCountyFromSpecimen(s)).filter(c => c)).size} counties
                 </span>
               ` : ''}
               ${species.specimens.some(s => s.media && s.media.length > 0) ? `
                 <span class="inline-block bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-2 py-1 rounded">
                   with images
                 </span>
               ` : ''}
             </div>
           </div>
         `;
       });
       
       // Add summary footer
       const totalSpecimens = selectedData.reduce((sum, sp) => sum + sp.specimens.length, 0);
       const totalCounties = new Set(selectedData.flatMap(sp => sp.specimens.map(spec => getCountyFromSpecimen(spec)).filter(c => c))).size;
       
       html += `
         <div class="mt-8 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
           <h4 class="font-semibold text-gray-900 dark:text-white mb-2">SUMMARY</h4>
           <p class="text-gray-700 dark:text-gray-300 text-sm">
             This report includes <strong>${selectedData.length} species</strong> with 
             <strong>${totalSpecimens} specimens</strong> from 
             <strong>${totalCounties} counties</strong> in Taiwan.
           </p>
           <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
             Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}
           </p>
         </div>
         </div> <!-- End of document-content -->
       `;
       
       previewLayout.innerHTML = html;
       previewLayout.classList.remove('hidden');
     }

     // Inline editing functions (make them global)
     window.toggleEditMode = function() {
       const displayMode = document.getElementById('display-mode');
       const editMode = document.getElementById('edit-mode');
       
       if (displayMode && editMode) {
         displayMode.classList.toggle('hidden');
         editMode.classList.toggle('hidden');
         
         // Pre-populate edit fields with current values
         const currentTitle = document.getElementById('display-title').textContent;
         const currentAuthor = document.getElementById('display-author').textContent;
         document.getElementById('edit-title-input').value = currentTitle;
         document.getElementById('edit-author-input').value = currentAuthor;
       }
     }
     
     window.saveDocumentInfo = function() {
       const newTitle = document.getElementById('edit-title-input').value.trim();
       const newAuthor = document.getElementById('edit-author-input').value.trim();
       
       if (!newTitle || !newAuthor) {
         alert('Please fill in both title and author');
         return;
       }
       
       // Update the display elements
       document.getElementById('display-title').textContent = newTitle;
       document.getElementById('display-author').textContent = newAuthor;
       
       // Update the namespace data
       namespacePart.title = newTitle;
       namespacePart.author = newAuthor;
       
       // Switch back to display mode
       toggleEditMode();
       
       // Show success message
       const saveBtn = document.getElementById('save-info-btn');
       const originalText = saveBtn.textContent;
       saveBtn.textContent = 'Saved!';
       saveBtn.className = 'bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md text-sm';
       
       setTimeout(() => {
         saveBtn.textContent = originalText;
         saveBtn.className = 'bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md text-sm';
       }, 1500);
     }
     
     window.cancelEditMode = function() {
       window.toggleEditMode();
     }
     
     window.goToFinalStep = function() {
       // Hide everything except the preview layout
       const sections = ['stepper-container', 'table-container', 'output-preview-section'];
       sections.forEach(sectionId => {
         const element = document.getElementById(sectionId);
         if (element) {
           element.style.display = 'none';
         }
       });
       
       // Show only the document content
       const documentContent = document.getElementById('document-content');
       const displayMode = document.getElementById('display-mode');
       const editMode = document.getElementById('edit-mode');
       
       if (documentContent && displayMode && editMode) {
         // Hide the edit section completely in final step
         document.querySelector('.mb-6.p-4.border').style.display = 'none';
         
         // Show a clean layout with just the document content
         const previewLayout = document.getElementById('preview-layout');
         const cleanContent = documentContent.innerHTML;
         
         // Add a back button and final layout
         previewLayout.innerHTML = `
           <div class="mb-4 flex justify-between items-center">
             <h1 class="text-3xl font-bold text-gray-900 dark:text-white">${namespacePart.title || 'Taxonomic Specimen Report'}</h1>
             <button onclick="goBackToPreview()" class="bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-md text-sm">
               ← Back to Edit
             </button>
           </div>
           <p class="mb-6 text-xl text-gray-700 dark:text-gray-300">Author: ${namespacePart.author || 'Unknown Author'}</p>
           ${cleanContent}
         `;
       }
     }
     
     window.goBackToPreview = function() {
       // Restore all sections
       const sections = ['stepper-container', 'table-container', 'output-preview-section'];
       sections.forEach(sectionId => {
         const element = document.getElementById(sectionId);
         if (element) {
           element.style.display = '';
         }
       });
       
       // Regenerate the preview layout
       const selectedData = [];
       speciesInfo.forEach((info, index) => {
         if (info.selectedSpecimens && info.selectedSpecimens.length > 0) {
           selectedData.push({
             species: namespacePart.items[index].item_title.scientific_name.canonical,
             speciesIndex: index,
             commonNames: namespacePart.items[index].commonNames || [],
             specimens: info.selectedSpecimens
           });
         }
       });
       
       generatePreviewLayout(selectedData);
     }

     // Preview tab switching
     window.switchPreviewTab = function(tabName) {
       // Update tab buttons
       document.querySelectorAll('.preview-tab-btn').forEach(btn => {
         if (btn.dataset.tab === tabName) {
           btn.className = 'py-2 px-1 border-b-2 border-blue-500 font-medium text-sm text-blue-600 dark:text-blue-400 preview-tab-btn';
         } else {
           btn.className = 'py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 preview-tab-btn';
         }
       });
       
       // Show/hide tab contents
       document.querySelectorAll('.preview-tab-content').forEach(content => {
         content.classList.add('hidden');
       });
       document.getElementById(`preview-${tabName}`).classList.remove('hidden');
     };

     // Download functions
     window.downloadPreview = function(format) {
       const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
       let content, filename, mimeType;
       
       if (format === 'txt') {
         content = document.getElementById('formatted-output').textContent;
         filename = `${timestamp}.txt`;
         mimeType = 'text/plain';
       } else if (format === 'json') {
         content = document.getElementById('json-output').textContent;
         filename = `${timestamp}.json`;
         mimeType = 'application/json';
       }
       
       const blob = new Blob([content], { type: mimeType });
       const url = URL.createObjectURL(blob);
       const a = document.createElement('a');
       a.href = url;
       a.download = filename;
       document.body.appendChild(a);
       a.click();
       document.body.removeChild(a);
       URL.revokeObjectURL(url);
     };

     // Copy to clipboard
     window.copyPreviewToClipboard = function() {
       const activeTab = document.querySelector('.preview-tab-btn[class*="border-blue-500"]').dataset.tab;
       const content = activeTab === 'formatted' 
         ? document.getElementById('formatted-output').textContent
         : document.getElementById('json-output').textContent;
       
       navigator.clipboard.writeText(content).then(() => {
         // Show feedback
         const btn = event.target;
         const originalText = btn.textContent;
         btn.textContent = 'Copied!';
         btn.classList.remove('text-green-600', 'hover:text-green-800');
         btn.classList.add('text-green-800');
         setTimeout(() => {
           btn.textContent = originalText;
           btn.classList.remove('text-green-800');
           btn.classList.add('text-green-600', 'hover:text-green-800');
         }, 2000);
       });
     };

     const renderPreviewLayout = (data) => {
       const title = document.getElementById('layout-title');
       title.textContent = data.title;
     }
     getSpecimenBtn.onclick = (e) => {
       e.preventDefault();
       fetchAllTBIAData();
     }
     selectSpecimensBtn.onclick = (e) => {
       e.preventDefault();
     }
     previewOutputBtn.onclick = (e) => {
       e.preventDefault();
       updateStepper(3);
     };

     // Table collapse/expand functions
     function collapseTable() {
       const tableContainer = document.getElementById('table-container');
       const collapseIcon = document.getElementById('table-collapse-icon');
       const collapseText = document.getElementById('table-collapse-text');
       
       if (tableContainer && collapseIcon && collapseText) {
         tableContainer.style.maxHeight = '0px';
         tableContainer.style.overflow = 'hidden';
         tableContainer.style.opacity = '0';
         collapseIcon.style.transform = 'rotate(-90deg)';
         collapseText.textContent = 'Show Table';
       }
     }

     function expandTable() {
       const tableContainer = document.getElementById('table-container');
       const collapseIcon = document.getElementById('table-collapse-icon');
       const collapseText = document.getElementById('table-collapse-text');
       
       if (tableContainer && collapseIcon && collapseText) {
         tableContainer.style.maxHeight = 'none';
         tableContainer.style.overflow = 'visible';
         tableContainer.style.opacity = '1';
         collapseIcon.style.transform = 'rotate(0deg)';
         collapseText.textContent = 'Hide Table';
       }
     }

     function toggleTable() {
       const tableContainer = document.getElementById('table-container');
       const isCollapsed = tableContainer.style.maxHeight === '0px';
       
       if (isCollapsed) {
         expandTable();
       } else {
         collapseTable();
       }
     }

     // Add event listener for table collapse button
     document.getElementById('table-collapse-btn').addEventListener('click', toggleTable);

     // Event listener for expandable rows
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

  init();

  
})();
