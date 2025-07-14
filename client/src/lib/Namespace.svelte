<script>
  const API_URL = import.meta.env.VITE_API_URL;

  import { speciesInfo, infoState } from '../shared.js';
  import NamespaceStep1 from './NamespaceStep1.svelte';
  import NamespaceStep2 from './NamespaceStep2.svelte';
  import NamespaceStep3 from './NamespaceStep3.svelte';

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

  let { namespaceId } = $props();
  let namespacePart = $state({});
  let isLoading = $state(true);
  let error = $state(null);
  let stepKey = $state(1);
  //let workingData = $state([]);
  //let recordsProgress = $state(namespacePart.items.map( x => ('init')));
  let steps = $state([
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
  ]);

  $effect(() => {
    const init = async () => {
      try {
        const response = await fetch(`${API_URL}/api/namespaces/${namespaceId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        let data = await response.json();
        namespacePart = data[0]; // get first
        namespacePart.items.forEach( x => {
          $speciesInfo.push({
            recid: x.taicol_usage_id,
            selectedIds: [],
            distributions: [],
            specimens: [],
            specimenData: [],
          });
          $infoState.push({
            progress: 'init',
            loading: false,
          });
        });
      } catch (e) {
        error = e.message;
      } finally {
        isLoading = false;
      }
    }
    init();
  });

  function handleToStep(toStep) {
    if (toStep > 0) {
      if (stepKey < steps.length) {
        stepKey += 1
      }
    } else {
      if (stepKey > 1) {
        stepKey -= 1
      }
    }
    steps.forEach( (v, i) => {
      if (i < stepKey) {
        v.status = 'completed';
      } else {
        v.status = 'pending';
      }
    });
    steps = [...steps];
  }

  function updateWorkingData(index, data) {
    workingData[index] = {
      ...workingData[index],
      ...data,
    };
  }
</script>

<div>
  {#if isLoading}
    <p>Loading TaiCOL namespace...</p>
  {:else if error}
    <p style="color: red;">Error: {error}</p>
  {:else}
    <DetailedStepper {steps} />
    <Hr />
    <Button onclick={() => handleToStep(-1)}>Previous Step<ArrowLeftOutline class="h-6 w-6" /></Button>
    <Button onclick={() => handleToStep(1)}>Next Step<ArrowRightOutline class="h-6 w-6" /></Button>
    {#if stepKey == 1}
      <NamespaceStep1 {namespacePart} />
    {:else if stepKey == 2}
      <NamespaceStep2 {namespacePart} />
    {:else if stepKey == 3}
      <NamespaceStep3 {namespacePart} />
    {/if}
  {/if}
</div>
