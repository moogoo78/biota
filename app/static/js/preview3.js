(function() {
  'use strict';
  console.log(document.referrer);

  let nameItemString = localStorage.getItem('nameItems');
  let nameItems = JSON.parse(nameItemString);
  let extensionString = localStorage.getItem('biotaExt');
  let extension = JSON.parse(extensionString);
  let nameItemsContainer = document.getElementById('nameItems');
  const template = document.querySelector('#item-name-template');

  nameItems.forEach( (item, index ) => {
    console.log(index, item);
    const clone = template.content.cloneNode(true);
    let canonicalName = clone.querySelector('#item-name-canonical');
    canonicalName.textContent = item.item_title.scientific_name.canonical;
    let nameIndex = clone.querySelector('#item-name-index');
    nameIndex.textContent = `${(index+1)}.`;

    let nameRemark = clone.querySelector('#item-name-remark');
    let nameRemarkText = '';
    if (item.item_title.name_remark) {
      nameRemarkText = item.item_title.name_remark;
    } else {
      nameRemarkText = item.item_title.display_name;
    }
    nameRemark.textContent = nameRemarkText;

    let commonName = clone.querySelector('#item-common-name');
    commonName.textContent = item.commonNames.join(', ');

    let description = clone.querySelector('#item-description');
    description.textContent = item.addFields.description;

    let synonymWrapper = clone.querySelector('#item-synonyms-wrapper');
    if (item.synonyms.length === 0) {
      synonymWrapper.style.display = 'none';
    }
    let synonymList = clone.querySelector('#item-synonyms');

    item.synonyms.forEach( x => {
      let li = document.createElement('li');
      li.textContent = `${x[0]} [${x[1]}]`;
      synonymList.appendChild(li);
    });

    let key = `${item.taicol_usage_id}`;
    if (key in extension) {
      let specimenWrapper = clone.querySelector('#item-specimen-wrapper');
      let distributionWrapper = clone.querySelector('#item-distribution-wrapper');
      if (extension[key].specimen.length === 0) {
        specimenWrapper.style.display = 'none';
      }
      if (extension[key].distribution.length === 0) {
        distributionWrapper.style.display = 'none';
      }
      console.log(extension[key].distribution);
      let specimen = clone.querySelector('#item-specimen');
      specimen.textContent = extension[key].specimenDisplay;
      let distribution = clone.querySelector('#item-distribution');
      distribution.textContent = extension[key].distribution.join(', ');
    }

    nameItemsContainer.appendChild(clone);
  });

})();
