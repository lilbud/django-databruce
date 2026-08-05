class Table {
  // The constructor initializes the object properties
  constructor(table, options, columns) {
    this.table = document.getElementById(table);
    this.options = options;
    this.columns = columns;
  }

  rowGroup(data, groupVal) {
    return Object.groupBy(data ?? [], (item) => item[groupVal]);
  };

  slugify(str) {
    if (!str) return '';

    return String(str)
      .toLowerCase() // Convert to lowercase
      .trim() // Trim leading/trailing whitespace
      .replace(/[^a-z0-9]+/g, '-') // Replace all spaces, underscores, and multiple hyphens with a single hyphen
      .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
  }

  async getData(url) {
    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(error);
    }
  }


}