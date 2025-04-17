/**
 * Populates the data / column select element
 */
Criteria.prototype._populateData = function () {
    var columns = this.s.dt.settings()[0].aoColumns;
    var includeColumns = this.s.dt
        .columns(this.c.columns)
        .indexes()
        .toArray();
 
    // Clear the data in the dropdown and append the title
    this.dom.data.empty().append(this.dom.dataTitle);
 
    // Create an array to store the options
    var options = [];
 
    for (var index = 0; index < columns.length; index++) {
        // Check that the column can be filtered on before adding it
        if (
            this.c.columns === true ||
            includeColumns.includes(index)
        ) {
            var col = columns[index];
            var opt = {
                index: index,
                origData: col.data,
                text: (
                    col.searchBuilderTitle || col.sTitle
                ).replace(/(<([^>]+)>)/gi, ''), // Remove any HTML tags
            };
 
            // Add option to the array
            options.push(opt);
        }
    }
 
    // Sort options alphabetically by text
    options.sort(function (a, b) {
        return a.text.localeCompare(b.text);
    });
 
    // Append sorted options to the dropdown
    options.forEach(function (opt) {
        var optionElement = $$3('<option>', {
            text: opt.text,
            value: opt.index,
        })
            .addClass(this.classes.option)
            .addClass(this.classes.notItalic)
            .prop('origData', opt.origData)
            .prop('selected', this.s.dataIdx === opt.index);
 
        this.dom.data.append(optionElement);
 
        // If the option is selected, remove 'selected' from the title
        if (this.s.dataIdx === opt.index) {
            this.dom.dataTitle.removeProp('selected');
        }
    }, this); // 'this' is passed as the second argument to retain context for 'this.classes'
};