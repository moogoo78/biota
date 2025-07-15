<script>
  const API_URL = import.meta.env.VITE_API_URL;
  import { speciesInfo, infoState } from '../shared.js';
  import {
    COUNTY_MAP,
    COUNTY_ORDER,
  } from './countyData.js';
  let { namespacePart } = $props();
  let progressColor = $state({
    init: 'orange',
    fetched: 'purple',
    selected: 'indigo',
    edited: 'teal'
  });
  let titles = {
    table: 'Found TBIA Specimens',
    form: 'Edit Specimen Data',
    image: 'Specimen Image',
  };
  //let isLoading = $state(true);
  let error = $state(null);
  let isModalOpen = $state(false);
  let modalView = $state('table');
  let modalTitle = $derived(titles[modalView]);
  let foundResults = $state({});
  let currentItemIndex = $state(-1);
  let currentSpecimenImage = $state('');

  import {
    Button,
    Checkbox,
    CloseButton,
    DescriptionList,
    Drawer,
    Heading,
    Indicator,
    Input,
    Label,
    List,
    Modal,
    P,
    Span,
    Table,
    TableHead,
    TableHeadCell,
    TableBody,
    TableBodyCell,
    TableBodyRow,
    Spinner,
  } from 'flowbite-svelte';

  async function findSpecimen(itemIndex, nameId, scientificName) {
    $infoState[itemIndex].loading = true;
    currentItemIndex = itemIndex;
    error = null;
    modalView = 'table';

    try {
      // find taxonKey
      const resp = await fetch(`${API_URL}/api/external/names/taicol/[${nameId}]${scientificName}`);
      const result = await resp.json();
      if (result.records.length > 0) {
        const taxonKey = result.records[0].key;
        console.log('get taxonKey:', taxonKey);

        const resp2 = await fetch(`${API_URL}/api/external/data/tbia/${taxonKey}`);
        const result2 = await resp2.json();

        if (result2.status === 'success') {

          $infoState[itemIndex].progress = 'feteched';
          $infoState[itemIndex].loading = false;

          let summaryDistribution = [];
          result2.records.forEach( record => {
            if ('adm2' in record.named_areas) {
              let k = record.named_areas.adm2;
              if (record.named_areas.adm2 in COUNTY_MAP) {
                k = COUNTY_MAP[record.named_areas.adm2].toUpperCase();
              }
              if (summaryDistribution.indexOf(k) < 0) {
              summaryDistribution.push(k);
              }
            }
          });
          const sortedDistribution = summaryDistribution.slice().sort((a, b) => {
            return COUNTY_ORDER.indexOf(a) - COUNTY_ORDER.indexOf(b);
          });
          foundResults = result2;
          isModalOpen = true;
          $speciesInfo[itemIndex].distributions = sortedDistribution;
        } else {
          error = 'fetch error';
          console.log(results2)
        }
      }
    } catch (err) {
      error = err.message;
      console.error(error);
      foundResults = {};
    } finally {
      //isLoading = false;
    }
  }
  function handleItemSelect(e, itemIndex, selectedIndex) {
    //console.log(e.target.checked, recordIndex);
    if (e.target.checked === true) {
      $speciesInfo[itemIndex].selectedIds.push(selectedIndex);
    } else {
      let idx = $speciesInfo[itemIndex].selectedIds.indexOf(selectedIndex);
      if (idx >= 0) {
        $speciesInfo[itemIndex].selectedIds.splice(idx, 1);
      }
    }

    if ($speciesInfo[itemIndex].selectedIds.length > 0) {
      $infoState[itemIndex].progress = 'selected';
    }
  }

  function handleModalOK(itemIndex) {
    if (modalView === 'table') {
      modalView = 'form';
    } else if (modalView === 'form') {
      const form = document.getElementById('specimen-form');
      const formData = new FormData(form);
      //console.log(form, formData);
      $speciesInfo[itemIndex].specimens = [];
      for (const [key, value] of formData) {
        const klist = key.split('-');
        if (klist[3] === 'input') {
          $speciesInfo[itemIndex].specimens.push(value);
          $infoState[itemIndex].progress = 'edited';
        } else if (klist[3] === 'data') {
          $speciesInfo[itemIndex].specimenData.push(JSON.parse(value));
        }
      }
      isModalOpen = false;
    } else if (modalView === 'image') {
      modalView = 'table';
    }
  }
</script>

<Table hoverable={true}>
  <TableHead>
    <TableHeadCell>Scientific Name</TableHeadCell>
    <TableHeadCell>Common Name</TableHeadCell>
    <TableHeadCell>Distributions</TableHeadCell>
    <TableHeadCell>Specimens</TableHeadCell>
    <TableHeadCell>Progress</TableHeadCell>
    <TableHeadCell>Actions</TableHeadCell>
  </TableHead>
  <TableBody>
    {#each namespacePart.items as item, index}
      <TableBodyRow>
        <TableBodyCell><P><Span italic>{item.item_title.scientific_name.canonical}</Span> {item.item_title.scientific_name.author}</P></TableBodyCell>
        <TableBodyCell>{item.commonNames}</TableBodyCell>
        <TableBodyCell>{$speciesInfo[index].distributions}</TableBodyCell>
        <TableBodyCell>{$speciesInfo[index].specimens}</TableBodyCell>
        <TableBodyCell><span class="flex items-center"><Indicator size="sm" color={progressColor[$infoState[index].progress]} class="me-1.5" />{$infoState[index].progress}</span></TableBodyCell>
        <TableBodyCell>
          <Button onclick={() => findSpecimen(index, item.taicol_taxon_name_id, item.item_title.scientific_name.canonical)}>{#if $infoState[index].loading}<Spinner class="me-3" size="4" /> {/if}Find Specimen</Button>
        </TableBodyCell>
      </TableBodyRow>
    {/each}
  </TableBody>
</Table>


<Modal title={modalTitle} bind:open={isModalOpen} size="xl">
  {#if modalView === 'table'}
    <div class="relative overflow-x-auto shadow-md sm:rounded-lg">
      <div class="flex flex-col sm:flex-row justify-between items-center text-sm text-gray-600 bg-gray-200 p-2">
        <div>
          共 {foundResults.total} 筆資料
        </div>
        <div class="mt-2 sm:mt-0">
          查詢時間：{new Date().toLocaleString('zh-TW')}
        </div>
      </div>
      <Table hoverable={true}>
        <TableHead>
          <TableHeadCell class="p-4!">
            <Checkbox />
          </TableHeadCell>
          <TableHeadCell>Media</TableHeadCell>
          <TableHeadCell>Calalog Number</TableHeadCell>
          <TableHeadCell>Collector</TableHeadCell>
          <TableHeadCell>Field Number</TableHeadCell>
          <TableHeadCell>Date</TableHeadCell>
          <TableHeadCell>Locality</TableHeadCell>
          <TableHeadCell>Dataset</TableHeadCell>
          <TableHeadCell>Source</TableHeadCell>
        </TableHead>
        <TableBody>
          {#each foundResults.records as record, recordIndex}
            <TableBodyRow>
              <TableBodyCell class="p-4!">
                <Checkbox onclick={(e) => handleItemSelect(e, currentItemIndex, recordIndex)} />
              </TableBodyCell>
            <TableBodyCell>{#if record.media.length > 0}<img src="{record.media[0]}" alt="specimen" onclick={() => {modalView = 'image'; currentSpecimenImage = record.media[0]}}/>{/if}</TableBodyCell>
              <TableBodyCell>{record.catalogNumber}</TableBodyCell>
              <TableBodyCell>{record.recordedBy}</TableBodyCell>
              <TableBodyCell>{record.recordNumber}</TableBodyCell>
              <TableBodyCell>{record.date}</TableBodyCell>
              <TableBodyCell>{record.locality}</TableBodyCell>
              <TableBodyCell>{record.datasetTitle}</TableBodyCell>
              <TableBodyCell><a href="{record.url}" class="hover:underline text-primary-600" target="_blank">link</a></TableBodyCell>
            </TableBodyRow>
          {/each}
        </TableBody>
      </Table>
    </div>
  {:else if modalView === 'form'}
    a{$speciesInfo[currentItemIndex].selectedIds}b
    {currentItemIndex}
    <form id="specimen-form">
      {#each $speciesInfo[currentItemIndex].selectedIds as selectId, selectedIndex}
        <Heading tag="h4">Specimen {selectedIndex+1}.</Heading>
        <!---<pre>{JSON.stringify(foundResults.records[selectId], null, 2)}</pre>-->

        <List tag="dl" class="divide-y divide-gray-200 text-gray-900 dark:divide-gray-700  dark:text-white">
          {#each Object.entries(foundResults.records[selectId]) as [key, value]}
            {#if ['specimen_display', 'named_areas', 'recid'].indexOf(key) < 0}
              <div class="flex flex-col pb-3">
                <DescriptionList tag="dt" class="mb-1">{key}</DescriptionList>
                <DescriptionList tag="dd">{value}</DescriptionList>
              </div>
            {/if}
          {/each}
        </List>
        <div>
          <Label for="specimen-{currentItemIndex}-{selectedIndex}" class="mb-2">Specimen Display Text</Label>
          <Input type="text" id="specimen-{currentItemIndex}-{selectedIndex}-input" name="specimen-{currentItemIndex}-{selectedIndex}-input"/>
          <Input type="hidden" id="specimen-{currentItemIndex}-{selectedIndex}-data" name="specimen-{currentItemIndex}-{selectedIndex}-data" value={JSON.stringify(foundResults.records[selectId])}/>
        </div>
      {/each}
    </form>
  {:else if modalView === 'image'}
    <img src={currentSpecimenImage} alt="specimen image"/>
  {/if}
  {#snippet footer()}
      <Button onclick={() => handleModalOK(currentItemIndex)}>OK</Button>
  {/snippet}
</Modal>
