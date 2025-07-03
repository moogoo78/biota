<script>
  import { PUBLIC_BACKEND_URL } from '$env/static/public';
  const { data } = $props();
  let sectionData = data.data[0];
  //console.log(sectionData);
  let recordsProgress = $state(sectionData.items.map( x => ('init')));
  let workingData = $state(sectionData.items.map( x => {
    return {
      recid: x.taicol_usage_id,
      selectedIds: [],
      distributions: [],
      specimens: [],
      specimenData: [],
    }
  }));

  let stepIndex = $state(0);
  //let isSidebarHide = $state(true);
  let loading = $state(false);
  let error = $state(null);
  let foundResults = $state({});

  let itemIndex = $state(-1);
  let modalStep = $state(0);
  let titles = ['Found TBIA Specimens', 'Edit Specimen Data'];
  let modalTitle = $derived(titles[modalStep]);
  let isModalOpen = $state(false);

  let progressColor = {
    init: 'orange',
    fetched: 'purple',
    selected: 'indigo',
    edited: 'teal',
  };

  let countyMap = {
    "彰化縣": "Changhua",
    "嘉義縣": "Chiayi",
    "新竹縣": "Hsinchu",
    "花蓮縣": "Hualien",
    "宜蘭縣": "Yilan",
    "金門縣": "Kinmen",
    "連江縣": "Lienchiang",
    "苗栗縣": "Miaoli",
    "南投縣": "Nantou",
    "澎湖縣": "Penghu",
    "屏東縣": "Pingtung",
    "臺東縣": "Taitung",
    "雲林縣": "Yunlin",
    "嘉義市": "Chiayi",
    "新竹市": "Hsinchu",
    "基隆市": "Keelung",
    "高雄市": "Kaohsiung",
    "新北市": "New Taipei",
    "桃園市": "Taoyuan",
    "臺南市": "Tainan",
    "臺北市": "Taipei",
    "臺中市": "Taichung"
  };
  const countyOrder = ['TAIPEI', 'KEELUNG', 'LIENCHIANG', 'NEW TAIPEI', 'YILAN', 'HSINCHU', 'TAOYUAN', 'MIAOLI', 'TAICHUNG', 'CHANGHUA', 'NANTOU', 'CHIAYI', 'YUNLIN', 'TAINAN', 'KAOHSIUNG', 'PENGHU', 'KINMEN', 'PINGTUNG', 'TAITUNG', 'HUALIEN'];

  import {
    Alert,
    Button,
    Checkbox,
    CloseButton,
    DetailedStepper,
    DescriptionList,
    Drawer,
    Heading,
    Hr,
    Indicator,
    Input,
    Label,
    List,
    Li,
    Modal,
    P,
    Span,
    Table,
    TableBody,
    TableBodyCell,
    TableBodyRow,
    TableHead,
    TableHeadCell,
    Timeline,
    TimelineItem,
    Textarea,
    Secondary,
    Spinner,
  } from 'flowbite-svelte';
  import {
    ArrowLeftOutline,
    ArrowRightOutline,
  } from "flowbite-svelte-icons";

  let steps = [
    {
      id: 1,
      label: "Get Source Data",
      description: "Fetch TaiCOL namespace data, preview",
      status: "completed"
    },
    {
      id: 2,
      label: "Search Specimens",
      description: "Search via TBIA portal API",
      status: "pending"
    },
    {
      id: 3,
      label: "Preview",
      description: "Check layout",
      status: "pending"
    },
    {
      id: 4,
      label: "Publish",
      description: "Publish to Public",
      status: "pending"
    }
  ];

  function handleToStep(toStep) {
    if (toStep > 0) {
      if (stepIndex < steps.length -1) {
        stepIndex += 1
      }
    } else {
      if (stepIndex > 0) {
        stepIndex -= 1
      }
    }
    steps.forEach( (v, i) => {
      if (i <= stepIndex) {
        v.status = 'completed';
      } else {
        v.status = 'pending';
      }
    });
    steps = [...steps];
  }


  async function findSpecimen(recordIndex, nameId, scientificName) {
    loading = true;
    error = null;
    itemIndex = recordIndex;
    modalStep = 0;

    try {
      // find taxonKey
      const resp = await fetch(`${PUBLIC_BACKEND_URL}/api/external/names/taicol/[${nameId}]${scientificName}`);
      const result = await resp.json();
      if (result.records.length > 0) {
        const taxonKey = result.records[0].key;
        console.log('get taxonKey:', taxonKey);

        const resp2 = await fetch(`${PUBLIC_BACKEND_URL}/api/external/data/tbia/${taxonKey}`);
        const result2 = await resp2.json();
        if (result2.status === 'success') {
          let summaryDistribution = [];
          result2.records.forEach( record => {
            if ('adm2' in record.named_areas) {
              let k = record.named_areas.adm2;
              if (record.named_areas.adm2 in countyMap) {
                k = countyMap[record.named_areas.adm2].toUpperCase();
              }
              if (summaryDistribution.indexOf(k) < 0) {
              summaryDistribution.push(k);
              }
            }
          });
          const sortedDistribution = summaryDistribution.slice().sort((a, b) => {
            return countyOrder.indexOf(a) - countyOrder.indexOf(b);
          });

          foundResults = result2;
          isModalOpen = true;
          workingData[recordIndex].distributions = sortedDistribution;
          //isSidebarHide = false;
          recordsProgress[recordIndex] = 'fetched'
        }
      }
    } catch (err) {
      error = err.message;
      foundResults = {};
    } finally {
      loading = false;
    }
  }

  // function clearData() {
  //   results = [];
  //   error = null;
  // }
  function handleItemSelect(e, idx, recordIndex) {
    //console.log(e.target.checked, recordIndex);
    if (e.target.checked === true) {
      workingData[idx].selectedIds.push(recordIndex);
    } else {
      let idx = workingData[idx].selectedIds.indexOf(recordIndex);
      if (idx >= 0) {
        workingData[idx].selectedIds.splice(idx, 1);
      }
    }

    if (workingData[idx].selectedIds.length > 0) {
      recordsProgress[idx] = 'selected';
    }
    //console.log(workingData);
  }

  function handleModalOK(recordIndex) {
    if (modalStep === 1) {
      const form = document.getElementById('specimen-form');
      const formData = new FormData(form);
      //console.log(form, formData);
      workingData[recordIndex].specimens = [];
      for (const [key, value] of formData) {

        const klist = key.split('-');
        if (klist[3] === 'input') {
          workingData[recordIndex].specimens.push(value);
          recordsProgress[recordIndex] = 'edited';
        } else if (klist[3] === 'data') {
          workingData[recordIndex].specimenData.push(JSON.parse(value));
        }
      }
      modalStep = 0;
      isModalOpen = false;
    }
    modalStep += 1;
  }
</script>


{#key stepIndex}
<DetailedStepper {steps} />
{/key}

<Hr />

<Button onclick={() => handleToStep(-1)}>Next Step<ArrowLeftOutline class="h-6 w-6" /></Button>
<Button onclick={() => handleToStep(1)}>Back Step<ArrowRightOutline class="h-6 w-6" /></Button>
<div class="flex justify-between items-center gap-2">
  <h1>{sectionData.title}</h1>
</div>
{stepIndex}
{#if stepIndex === 0 || stepIndex === 2}
  {#if sectionData.literatures.length > 0}
    <Heading tag="h2" class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">LITERATURES</Heading>
    <List tag="ul" class="space-y-1 text-gray-500 dark:text-gray-400">
      {#each sectionData.literatures as i}
        <Li>{i.content} | {i.short_author}</Li>
      {/each}
    </List>
  {/if}

  {#each sectionData.items as item, index}
    <Heading tag="h4" class="mt-4">{index+1}. {item.item_title.display_name}</Heading>

    {#if item.synonyms.length > 0}
      <Heading tag="h5" class="mt-4 mb-2">Synonyms</Heading>
      <List>
        {#each item.synonyms as i}
          <Li>{i[0]}</Li>
        {/each}
      </List>
    {/if}

     {#if item.commonNames}
      <Heading tag="h5" class="mt-4">Common Names</Heading>
      <P class="mb-8" weight="light" color="text-gray-100">{item.commonNames}</P>
    {/if}
    <Heading tag="h5" class="mt-4">Description</Heading>
    <P class="mb-8" weight="light" color="text-gray-500">{item.addFields.description}</P>


    {#if stepIndex == 2}
      <h3>Distributions</h3>
      {workingData[index].distributions}
      <h3>Specimens</h3>
      {workingData[index].specimens}
    {/if}
  {/each}
{:else if stepIndex === 1}
  {#if loading}
    <Spinner class="mr-2" size="4" />
    loading...
  {/if}
  {#if error}
    <Alert color="red" class="mb-4">
      <span class="font-medium">錯誤！</span> {error}
    </Alert>
  {/if}
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
      {#each sectionData.items as item, index}
        <TableBodyRow>
          <TableBodyCell><P><Span italic>{item.item_title.scientific_name.canonical}</Span> {item.item_title.scientific_name.author}</P></TableBodyCell>
          <TableBodyCell>{item.commonNames}</TableBodyCell>
          <TableBodyCell>{workingData[index].distributions}</TableBodyCell>
          <TableBodyCell>{workingData[index].specimens}</TableBodyCell>
          <TableBodyCell><span class="flex items-center"><Indicator size="sm" color="{progressColor[recordsProgress[index]]}" class="me-1.5" />{recordsProgress[index]}</span></TableBodyCell>
          <TableBodyCell>
            <Button onclick={() => findSpecimen(index, item.taicol_taxon_name_id, item.item_title.scientific_name.canonical)}>Find Specimen</Button>
          </TableBodyCell>
        </TableBodyRow>
      {/each}
    </TableBody>
  </Table>
{/if}






<Modal title="{modalTitle}" bind:open={isModalOpen} size="xl">
  {#if modalStep === 0}
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
                <Checkbox onclick={(e) => handleItemSelect(e, itemIndex, recordIndex)} />
              </TableBodyCell>
            <TableBodyCell>{#if record.media.length > 0}<img src="{record.media[0]}">{/if}</TableBodyCell>
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
  {:else if modalStep === 1}
    <form id="specimen-form">
      {#each workingData[itemIndex].selectedIds as selectId, selectedIndex}
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
          <Label for="specimen-{itemIndex}-{selectedIndex}" class="mb-2">Specimen Display Text</Label>
          <Input type="text" id="specimen-{itemIndex}-{selectedIndex}-input" name="specimen-{itemIndex}-{selectedIndex}-input"/>
          <Input type="hidden" id="specimen-{itemIndex}-{selectedIndex}-data" name="specimen-{itemIndex}-{selectedIndex}-data" value="{JSON.stringify(foundResults.records[selectId])}"/>
        </div>
      {/each}
    </form>
  {/if}
  {#snippet footer()}
      <Button onclick={() => handleModalOK(itemIndex)}>OK</Button>
  {/snippet}
</Modal>
