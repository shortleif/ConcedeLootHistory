function createAccordion(accordionId, headingId, headingText, parent) {
  const accordionDiv = document.createElement('div');
  accordionDiv.classList.add('accordion');
  accordionDiv.id = accordionId;

  const cardHeader = document.createElement('div');
  cardHeader.classList.add('accordion-header', 'custom-card-header');
  cardHeader.id = headingId;

  const accordionButton = document.createElement('div');
  accordionButton.classList.add('accordion-button', 'collapsed');
  accordionButton.type = 'button';
  accordionButton.dataset.bsToggle = 'collapse';
  accordionButton.dataset.bsTarget = `#collapse-${accordionId}`;
  accordionButton.setAttribute('aria-expanded', 'false');
  accordionButton.setAttribute('aria-controls', `#collapse-${accordionId}`);
  accordionButton.textContent = headingText;

  cardHeader.appendChild(accordionButton);
  accordionDiv.appendChild(cardHeader);

  // Create the content for the accordion
  const collapseDiv = document.createElement('div');
  collapseDiv.classList.add('collapse');
  collapseDiv.id = `collapse-${accordionId}`;
  collapseDiv.setAttribute('aria-labelledby', headingId);
  collapseDiv.setAttribute('data-parent', `#${parent}`);

  const cardBody = document.createElement('div');
  cardBody.classList.add('card-body');

  collapseDiv.appendChild(cardBody);
  accordionDiv.appendChild(collapseDiv);

  return { accordionDiv, cardBody, collapseDiv };
}

function processLoot(characterData, specType, cardBody, raid) {
  const heading = document.createElement('h3');
  heading.textContent = `${specType} Loot`;
  cardBody.appendChild(heading);

  const table = createTable(['table', 'table-dark']);
  const headerRow = createTableRow([
    createElement('th', 'Item Name'),
    createElement('th', 'Looted On'),
    createElement('th', '# Looted'),
    ...(specType === 'Mainspec' ? [createElement('th', 'Soft-reserved?')] : []), // Add new column header only for Mainspec
  ]);
  table.appendChild(headerRow);

  // Check if characterData[specType] exists before proceeding
  if (characterData[specType]) {
    const items = Object.values(characterData[specType])
      .filter((item) => item.raid === raid)
      .sort((a, b) => a.itemName.localeCompare(b.itemName));

    for (const item of items) {
      const itemId = Object.keys(characterData[specType]).find(
        (key) => characterData[specType][key] === item
      );
      const itemRow = createTableRow([
        createElement(
          'td',
          null,
          createLink(
            `https://www.wowhead.com/classic/item=${itemId}`,
            item.itemName
          )
        ),
        createElement(
          'td',
          item.lootEvents
            .map((event) => event.dateTime)
            .flat()
            .join(', ')
        ),
        createElement(
          'td',
          item.lootEvents
            .map((event) => event.timesLooted)
            .reduce((sum, current) => sum + current, 0)
        ),
        ...(specType === 'Mainspec'
          ? [
              createElement(
                'td',
                item.lootEvents.some((event) => event.softReserved)
                  ? 'Yes'
                  : 'No'
              ),
            ]
          : []), // Add new column data only for Mainspec
      ]);
      table.appendChild(itemRow);
    }
  }

  cardBody.appendChild(table);
}

function createTable(tableClasses) {
  const table = document.createElement('table');
  table.classList.add(...tableClasses); // Add 'total' class here
  return table;
}

function createTableRow(cells) {
  const row = document.createElement('tr');
  cells.forEach((cell) => row.appendChild(cell));
  return row;
}

function createElement(tag, textContent, child) {
  const element = document.createElement(tag);
  if (textContent) {
    element.textContent = textContent;
  }
  if (child) {
    element.appendChild(child);
  }
  return element;
}

function createLink(href, textContent) {
  const link = document.createElement('a');
  link.href = href;
  link.target = '_blank';
  link.textContent = textContent;
  return link;
}

fetch('../raid_data.json')
  .then((response) => response.json())
  .then((raidData) => {
    const lootDataDiv = document.getElementById('loot-data');

    // Get all unique raid names
    const raids = new Set();
    for (const character in raidData) {
      for (const itemId in raidData[character].Mainspec) {
        raids.add(raidData[character].Mainspec[itemId].raid);
      }
      for (const itemId in raidData[character].Offspec) {
        raids.add(raidData[character].Offspec[itemId].raid);
      }
    }
    const sortedRaids = Array.from(raids).sort();

    sortedRaids.forEach((raid) => {
      const { accordionDiv, cardBody: raidCardBody } = createAccordion(
        `accordion-${raid}`,
        `heading-${raid}`,
        raid,
        `accordion-${raid}`
      );
      lootDataDiv.appendChild(accordionDiv);

      // Find characters who have loot for this raid
      const charactersInRaid = Object.keys(raidData)
        .filter((character) => {
          const mainspecLoot = raidData[character].Mainspec
            ? Object.values(raidData[character].Mainspec)
            : [];
          const offspecLoot = raidData[character].Offspec
            ? Object.values(raidData[character].Offspec)
            : [];
          return mainspecLoot
            .concat(offspecLoot)
            .some((item) => item.raid === raid);
        })
        .sort();

      charactersInRaid.forEach((character) => {
        const {
          accordionDiv: characterAccordionDiv,
          cardBody: characterCardBody,
        } = createAccordion(
          `accordion-${character}`,
          `heading-${character}`,
          character,
          `accordion-${character}`
        );
        raidCardBody.appendChild(characterAccordionDiv);

        processLoot(raidData[character], 'Mainspec', characterCardBody, raid); // Pass raid to processLoot
        processLoot(raidData[character], 'Offspec', characterCardBody, raid); // Pass raid to processLoot
      });
    });

    const allDates = [];
    for (const character in raidData) {
      const characterData = raidData[character];
      const mainspecDates = Object.values(characterData.Mainspec)
        .flatMap((item) => item.lootEvents)
        .flatMap((event) => event.dateTime);
      const offspecDates = Object.values(characterData.Offspec)
        .flatMap((item) => item.lootEvents)
        .flatMap((event) => event.dateTime);
      allDates.push(...mainspecDates, ...offspecDates);
    }
    const latestDate = allDates.sort().pop();

    const { accordionDiv: latestAccordionDiv, cardBody: latestCardBody } =
      createAccordion(
        'accordion-latest',
        'heading-latest',
        `Loot from latest raid (${latestDate})`,
        'accordion-latest'
      );
    lootDataDiv.prepend(latestAccordionDiv);

    // Start Latest Table //

    const latestLootTable = createTable(['table', 'table-dark', 'latest']);
    const tableBody = document.createElement('tbody');
    latestLootTable.appendChild(tableBody);
    const latestLootHeaderRow = createTableRow([
      createElement('th', 'Name'),
      createElement('th', 'Items'),
      createElement('th', 'Soft-reserved?'), // Add new column header
    ]);
    tableBody.appendChild(latestLootHeaderRow);

    const characterLoot = {};
    for (const character in raidData) {
      const characterData = raidData[character];
      characterLoot[character] = [];

      const mainspecItems = (
        characterData.Mainspec && Object.keys(characterData.Mainspec).length > 0
          ? Object.values(characterData.Mainspec)
          : []
      )
        .filter((item) =>
          item.lootEvents.some((event) => event.dateTime.includes(latestDate))
        )
        .map((item) => ({
          itemName: item.itemName,
          softReserved: item.lootEvents.some((event) => event.softReserved),
        }));

      const offspecItems = (
        characterData.Offspec && Object.keys(characterData.Offspec).length > 0
          ? Object.values(characterData.Offspec)
          : []
      )
        .filter((item) =>
          item.lootEvents.some((event) => event.dateTime.includes(latestDate))
        )
        .map((item) => ({
          itemName: item.itemName,
          softReserved: item.lootEvents.some((event) => event.softReserved),
        }));

      characterLoot[character] = mainspecItems.concat(offspecItems);
    }

    for (const character in characterLoot) {
      const items = characterLoot[character]
        .map(
          (item) =>
            `${item.itemName} (Soft-reserved: ${
              item.softReserved ? 'Yes' : 'No'
            })`
        )
        .join(', ');

      const row = createTableRow([
        createElement('td', character),
        createElement('td', items),
      ]);
      tableBody.appendChild(row);
    }

    latestCardBody.appendChild(latestLootTable);
  })
  .catch((error) => {
    console.error('Error fetching or processing data:', error);
  });

fetch('../softres_data.json')
  .then((response) => response.json())
  .then((srData) => {
    const {
      accordionDiv: srtopAccordionDiv,
      cardBody: srtopCardBody,
      collapseDiv: srtopCollapseDiv,
    } = createAccordion(
      'accordion-softres',
      'heading-softres',
      'SR Toplist This Phase',
      'accordion-softres'
    );

    // Create the table element
    const srtopTable = createTable(['table', 'table-dark', 'sr-top']);
    const srtopTableBody = document.createElement('tbody');
    srtopTable.appendChild(srtopTableBody);

    // Create the table header row
    const srtopHeaderRow = createTableRow([
      createElement('th', 'Item'),
      createElement('th', 'Boss'),
      createElement('th', 'Times Reserved'),
    ]);
    srtopTableBody.appendChild(srtopHeaderRow);

    makeTableSortable(srtopTable);

    // Aggregate the data by item and boss
    const aggregatedData = {};

    for (const raidInstance in srData) {
      for (const boss in srData[raidInstance]) {
        for (const player in srData[raidInstance][boss]) {
          for (const item in srData[raidInstance][boss][player]) {
            const itemData = srData[raidInstance][boss][player][item];
            const numReserved = itemData.item_info['Number reserved'];

            if (!aggregatedData[item]) {
              aggregatedData[item] = {};
            }

            if (!aggregatedData[item][boss]) {
              aggregatedData[item][boss] = 0;
            }

            aggregatedData[item][boss] += numReserved;
          }
        }
      }
    }

    // Process the aggregated data and populate the table
    for (const item in aggregatedData) {
      for (const boss in aggregatedData[item]) {
        const numReserved = aggregatedData[item][boss];
        const row = createTableRow([
          createElement('td', item),
          createElement('td', boss),
          createElement('td', numReserved.toString()),
        ]);
        srtopTableBody.appendChild(row);
      }
    }

    // Add the table to the accordion card body
    srtopCardBody.appendChild(srtopTable);

    // Append the accordion to the softres div
    const softresDiv = document.getElementById('softres');
    softresDiv.appendChild(srtopAccordionDiv);

    // Create the h2 element for the "Softreserves" heading
    const srHeading = document.createElement('h2');
    srHeading.textContent = 'Soft-reserves';

    // Append the heading and the accordion to the desired container
    softresDiv.prepend(srHeading); // Append the heading first
  })
  .catch((error) => {
    console.error('Error fetching or processing data:', error);
  });

function makeTableSortable(table) {
  const headers = table.querySelectorAll('th');
  let currentSortColumn = null;
  let sortAscending = true;

  headers.forEach((header) => {
    header.addEventListener('click', () => {
      const columnIndex = Array.from(header.parentNode.children).indexOf(
        header
      );

      if (currentSortColumn === columnIndex) {
        sortAscending = !sortAscending;
      } else {
        currentSortColumn = columnIndex;
        sortAscending = true;
      }

      const rows = Array.from(
        table.querySelectorAll('tbody tr:not(:first-child)')
      );
      rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.toLowerCase();
        const bValue = b.children[columnIndex].textContent.toLowerCase();

        // Convert values to numbers if they are numeric
        const aNum = isNaN(aValue) ? aValue : parseFloat(aValue);
        const bNum = isNaN(bValue) ? bValue : parseFloat(bValue);

        if (aNum < bNum) {
          return sortAscending ? -1 : 1;
        } else if (aNum > bNum) {
          return sortAscending ? 1 : -1;
        } else {
          return 0;
        }
      });

      // Remove existing rows and append sorted rows
      const tbody = table.querySelector('tbody');
      const headerRow = tbody.querySelector('tr:first-child'); // Save the header row
      tbody.innerHTML = '';
      tbody.appendChild(headerRow); // Re-append the header row
      rows.forEach((row) => tbody.appendChild(row));
    });
  });
}
