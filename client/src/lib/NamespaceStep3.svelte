<script>
  import { speciesInfo, infoState } from '../shared.js';
  let { namespacePart } = $props();

  import {
    Heading,
    List,
    Li,
    P,
  } from 'flowbite-svelte';
</script>


{#if namespacePart.literatures.length > 0}
  <Heading tag="h2" class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">LITERATURES</Heading>
  <List tag="ul" class="space-y-1 text-gray-500 dark:text-gray-400">
    {#each namespacePart.literatures as i}
      <Li>{i.content} | {i.short_author}</Li>
    {/each}
  </List>
{/if}

{#each namespacePart.items as item, index}
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

  <h3>Distributions</h3>
  {$speciesInfo[index].distributions.join(', ')}

  <h3>Specimens</h3>
  {$speciesInfo[index].specimens.join(', ')}
{/each}

