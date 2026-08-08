/*! CardView 1.0.1 for DataTables
 * Copyright (c) SpryMedia Ltd - https://datatables.net/license/plus
 */

(function (factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD
    define(['datatables.net'], function (dt) {
      return factory(window, document, dt);
    });
  }
  else if (typeof exports === 'object') {
    // CommonJS
    var cjsRequires = function (root) {
      if (!root.DataTable) {
        require('datatables.net')(root);
      }
    };

    if (typeof window === 'undefined') {
      module.exports = function (root) {
        if (!root) {
          // CommonJS environments without a window global must pass a
          // root. This will give an error otherwise
          root = window;
        }

        cjsRequires(root);
        return factory(root, root.document, root.DataTable);
      };
    }
    else {
      cjsRequires(window);
      module.exports = factory(window, window.document, window.DataTable);
    }
  }
  else {
    // Browser
    factory(window, document, window.DataTable);
  }
}(function (window, document, DataTable) {
  'use strict';

  var Dom = DataTable.Dom;
  var Api = DataTable.Api;
  var util = DataTable.util;

  /*
   * Icons used by CardView
   */
  function wrap(paths) {
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
      paths +
      '</svg>');
  }
  const icons = {
    tick: wrap('<path d="M20 6 9 17l-5-5"/>')
  };

  const ulList = function () {
    let card = Dom.c('div')
      .classAdd(this.classes.card)
      .attr('data-dt-row', '')
      .append(Dom.c('div')
        .classAdd(this.classes.selector)
        .html(CardView.icons.tick))
      .append(Dom.c('div')
        .classAdd(this.classes.cardContent)
        .append(Dom.c('ul').append(Dom.c('li')
          .attr('data-dtcv-for', 'columns')
          .attr('data-dt-column', '')
          .append(Dom.c('span')
            .classAdd(this.classes.title)
            .attr('data-dtcv-title', ''))
          .append(Dom.c('span')
            .classAdd(this.classes.data)
            .attr('data-dtcv-dataSrc', '')))));
    return card;
  };
  const dlList = function () {
    let card = Dom.c('div')
      .classAdd(this.classes.card)
      .attr('data-dt-row', '')
      .append(Dom.c('div')
        .classAdd(this.classes.selector)
        .html(CardView.icons.tick))
      .append(Dom.c('div')
        .classAdd(this.classes.cardContent)
        .append(Dom.c('dl').append(Dom.c('div')
          .attr('data-dtcv-for', 'columns')
          .attr('data-dt-column', '')
          .append(Dom.c('dt')
            .classAdd(this.classes.title)
            .attr('data-dtcv-title', ''))
          .append(Dom.c('dd')
            .classAdd(this.classes.data)
            .attr('data-dtcv-dataSrc', '')))));
    return card;
  };
  const miniTable = function () {
    let card = Dom.c('div')
      .classAdd(this.classes.card)
      .attr('data-dt-row', '')
      .append(Dom.c('div')
        .classAdd(this.classes.selector)
        .html(CardView.icons.tick))
      .append(Dom.c('div')
        .classAdd(this.classes.cardContent)
        .append(Dom.c('table').append(Dom.c('tr')
          .attr('data-dtcv-for', 'columns')
          .attr('data-dt-column', '')
          .append(Dom.c('td')
            .classAdd(this.classes.title)
            .attr('data-dtcv-title', ''))
          .append(Dom.c('td')
            .classAdd(this.classes.data)
            .attr('data-dtcv-dataSrc', '')))));
    return card;
  };


  if (!DataTable || !DataTable.versionCheck || !DataTable.versionCheck('3')) {
    throw 'Warning: CardView requires DataTables 3 or greater';
  }
  class CardView {
    /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
     * Public methods (exposed via the DataTables API below)
     */
    /**
     *
     * @returns Determine if card view is shown or not
     */
    displayed() {
      return this.s.displayed;
    }
    mode(mode) {
      if (mode === undefined) {
        return this.s.mode;
      }
      this.s.mode = mode;
      if (mode === 'cards') {
        this._display();
      }
      else if (mode === 'table') {
        this._hide();
      }
      else {
        this._resize();
      }
      this.s.dt.trigger('cardView-mode', [mode]);
      DataTable.plus('2026-08-04');
      return this;
    }
    /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
     * Constructor
     */
    constructor(dtIn, opts) {
      let dt = new DataTable.Api(dtIn);
      let ctx = dt.settings()[0];
      let tableHost = Dom.s(dt.table().node())
        .closest('.dt-layout-table')
        .children('div');
      this.c = util.object.assignDeep({}, CardView.defaults, opts);
      this.classes = Object.assign({}, CardView.classes);
      this.s = {
        columnCount: 1,
        displayed: false,
        dt: dt,
        mode: this.c.mode,
        restorePageLen: dt.page.len()
      };
      this.dom = {
        container: Dom.c('div').classAdd(this.classes.container),
        host: tableHost,
        table: tableHost.children(':not(.dt-processing)'),
        templateSrc: typeof this.c.template === 'function'
          ? this.c.template.call(this)
          : Dom.s(this.c.template),
        template: null
      };
      this.dom.container.prependTo(this.dom.host);
      if (ctx._cardView) {
        return;
      }
      ctx._cardView = this;
      // Go!
      this._init();
    }
    /* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
     * Private methods
     */
    /**
     * Calculate the number of columns that should be shown
     */
    _columns() {
      let width = Dom.s(this.s.dt.table().container()).width();
      let breakpoints = this.c.breakpoints;
      let columns;
      let breakpoint = 'tiny';
      if (width >= breakpoints[0]) {
        breakpoint = 'huge';
      }
      else if (width >= breakpoints[1]) {
        breakpoint = 'large';
      }
      else if (width >= breakpoints[2]) {
        breakpoint = 'medium';
      }
      else if (width >= breakpoints[3]) {
        breakpoint = 'small';
      }
      else {
        breakpoint = 'tiny';
      }
      // Number of columns
      columns = this.c.gridColumns[breakpoint];
      this.s.columnCount = columns;
      this.dom.container[0].style.setProperty('--dtcv-grid_columns', columns.toString());
    }
    /**
     * Show the card view and hide the table
     */
    _display() {
      this.dom.container.css('display', '');
      this.dom.table.css('display', 'none');
      this.s.displayed = true;
      this._pageLength();
      Dom.s(this.s.dt.table().container()).classAdd(this.classes.shown);
      this.s.dt.trigger('cardView-display', ['cards']);
    }
    _destroy() {
      let dt = this.s.dt;
      if (this.displayed()) {
        this._hide();
      }
      this.dom.container.off('.cardView').remove();
      dt.off('.cardView');
    }
    /**
     * Draw the cards for the current page
     */
    _draw() {
      let that = this;
      let dt = this.s.dt;
      this.dom.container.empty();
      dt.rows({ page: 'current' }).every(function () {
        that._renderCard(this);
      });
    }
    /**
     * Hide the card view and switch back to the table
     */
    _hide() {
      this.dom.table.css('display', '');
      this.dom.container.css('display', 'none');
      this.s.displayed = false;
      this._pageLength();
      Dom.s(this.s.dt.table().container()).classRemove(this.classes.shown);
      this.s.dt.trigger('cardView-display', ['table']);
    }
    /**
     * Initialise the instance
     */
    _init() {
      var _a;
      let dt = this.s.dt;
      DataTable.plus('2026-08-04');
      let loadedState = (_a = dt.state.loaded()) === null || _a === void 0 ? void 0 : _a.cardView;
      let mode = loadedState ? loadedState.mode : this.c.mode;
      this._columns();
      this.mode(mode);
      this._selectMode();
      this._selectEvents();
      dt.on('column-sizing.cardView', () => {
        this._resize();
      })
        .on('draw.cardView', () => {
          if (this.s.displayed) {
            this._draw();
          }
        })
        .on('rowInvalidate.cardView', (e, ctx, rowIdx) => {
          this._updateCard(rowIdx);
        })
        .on('selectStyle.cardView', () => {
          this._selectMode();
        })
        .on('stateSaveParams.cardView', (e, s, data) => {
          if (!data.cardView) {
            data.cardView = {};
          }
          data.cardView.mode = this.s.mode;
        })
        .on('destroy.cardView', () => {
          this._destroy();
        });
    }
    /**
     * Update page lengths to fit the card grid.
     */
    _pageLength() {
      // Check if any changes should be made - core (i.e. DataTables) means
      // that CardView will use the core library's page lengths - i.e. no
      // changes.
      if (this.c.pageLength === 'core') {
        return;
      }
      // Otherwise, we want to round the page lengths to the nearest value
      // that will fit the grid view.
      let dt = this.s.dt;
      let selects = Dom.s(dt.table().container()).find('div.dt-length select');
      let columns = this.s.columnCount;
      let selected = this.s.restorePageLen;
      if (selects.length) {
        // Undo any changes we've previously made
        selects.find('option').each(optionEl => {
          let option = Dom.s(optionEl);
          let original = option.data('dtcvOriginal');
          if (original) {
            option.attr('value', original).text(original.toString());
          }
        });
        // Update each page length option to the closest that will fit in the
        // current grid as a whole number
        if (this.s.displayed) {
          selects.find('option').each(optionEl => {
            let option = Dom.s(optionEl);
            let original = parseInt(option.attr('value'));
            let mod = original % columns;

            if (mod !== 0) {
              let write = Math.round(original / columns) * columns;
              option
                .attr('value', write)
                .text(write.toString())
                .data('dtcvOriginal', original);
            }
          });
        }
        // If the table isn't yet ready, then we used the stored value (init
        // or state)
        if (!dt.ready()) {
          selects.val(this.s.restorePageLen);
          selected = this.s.restorePageLen;
        }
        else {
          // If the page length has changed, we need to redraw the table
          selected = parseInt(selects.val());
        }
        // On initialisation if the mode is switched and the value doesn't
        // exist in the menu, we need to compute it from the API
        if (!selected) {
          selected = Math.round(dt.page.len() / columns) * columns;
          selects.val(selected);
        }
      }
      else if (this.s.displayed) {
        // No page length input, so we just work from the API
        let current = dt.page.len();
        selected = Math.round(current / columns) * columns;
      }
      if (selected !== dt.page.len()) {
        dt.page.len(selected);
        if (dt.ready()) {
          dt.draw(false);
        }
      }
      else if (this.dom.container.children().length === 0 &&
        dt.page.info().recordsDisplay &&
        this.s.displayed &&
        dt.ready()) {
        this._draw();
      }
    }
    /**
     * Set the number of columns to use for the display, based on the width
     * of the table's viewport.
     *
     * This works by setting a CSS property, thus allowing any number of columns
     * without needing lots of (almost) duplicate CSS.
     */
    _resize() {
      this._columns();
      // Auto activation
      let width = Dom.s(this.s.dt.table().container()).width();
      let autoResponsive = this.c.responsiveBreakpoint;
      if (this.s.mode === 'auto') {
        let bp;
        // The configuration option can be a number of different types -
        // need to resolve to a number for the logic below.
        if (typeof autoResponsive === 'number') {
          bp = autoResponsive;
        }
        else if (autoResponsive === true || autoResponsive === 'medium') {
          bp = this.c.breakpoints[2];
        }
        else if (autoResponsive === 'huge') {
          bp = this.c.breakpoints[0];
        }
        else if (autoResponsive === 'large') {
          bp = this.c.breakpoints[1];
        }
        else if (autoResponsive === 'small') {
          bp = this.c.breakpoints[3];
        }
        else {
          bp = this.c.breakpoints[4];
        }
        if (width < bp && !this.displayed()) {
          this._display();
        }
        else if (width >= bp && this.displayed()) {
          this._hide();
        }
      }
      this._pageLength();
    }
    /**
     * Event handlers for syncing row selection between CardView and the table
     */
    _selectEvents() {
      let dt = this.s.dt;
      // Click on selection element. Rather than adding classes here, we use
      // the DataTables API to select the row, which triggers events which are
      // then used below to update the card classes.
      this.dom.container.on('click.cardView', 'div.' + this.classes.selector.replace(/ /, '.'), function (e) {
        let rowIdx = parseInt(Dom.s(this).closest('[data-dt-row]').attr('data-dt-row'));
        if (typeof rowIdx === 'number') {
          let row = dt.row(rowIdx);
          if (row.selected()) {
            row.deselect();
          }
          else {
            row.select();
          }
        }
      });
      dt.on('select.cardView deselect.cardView', (e, dtEvt, type, indexes) => {
        let ctxData = dt.settings()[0].data;
        if (type === 'row') {
          for (let i = 0; i < indexes.length; i++) {
            let card = ctxData[indexes[i]]._card;
            if (card) {
              card.classToggle(this.classes.selected, e.type === 'select');
            }
          }
        }
      });
    }
    /**
     * Update CardView for the table selection mode changing
     */
    _selectMode() {
      let dt = this.s.dt;
      // If no select, then can't be selectable
      if (!dt.select) {
        return;
      }
      // Add a class if the items should be selectable
      this.dom.container.classToggle(this.classes.selectable, dt.select.style() !== 'api');
    }
    /**
     * Set a matched attribute's value based for an element, matched from the
     * host element and its children.
     *
     * @param el Element (and children) to search for the given attribute
     * @param attr Attribute to search for
     * @param value Value to apply
     */
    _templateAttr(el, attr, value) {
      let els = el.find('[data-' + attr + ']');
      if (el.attr('data-' + attr) !== null) {
        els.add(el);
      }
      els.each(matchedEl => {
        matchedEl.setAttribute('data-' + attr, value);
      });
    }
    /**
     * Set the HTML content of an element with a given data attribute
     *
     * @param el Element (and children) to search for the given attribute
     * @param attr Attribute to search for
     * @param value Content to set
     */
    _templateHtml(el, attr, value) {
      let els = el.find('[data-' + attr + ']');
      if (el.attr('data-' + attr) !== null) {
        els.add(el);
      }
      els.each(matchedEl => {
        let matched = Dom.s(matchedEl);
        let attrVal = matched.attr('data-' + attr);
        let colIdx = matched.attr('data-dt-column')
          ? matched.attr('data-dt-column')
          : matched.closest('[data-dt-column]').attr('data-dt-column');
        matched.html(typeof value === 'function'
          ? value(attrVal, colIdx !== null ? parseInt(colIdx) : null)
          : value.toString());
      });
    }
    /**
     * Take a template and complete any "macro" attributes, preparing it for use
     * as the card template
     *
     * @returns An element that can be used as the template source to be cloned
     *   and filled in for each record to be displayed.
     */
    _templatePrep() {
      if (this.dom.template) {
        return this.dom.template;
      }
      let that = this;
      let dt = this.s.dt;
      let src = this.dom.templateSrc;
      let cloned = src[0].nodeName.toLowerCase() === 'template'
        ? Dom.s(document.importNode(src[0].content, true)).children()
        : src.clone(true);
      cloned.find('[data-dtcv-for]').each(forNode => {
        let host = forNode.parentElement;
        let forEl = Dom.s(forNode);
        forEl.detach().attrRemove('data-dtcv-for');
        dt.columns(this.c.columns).every(function () {
          let entryClone = forEl.clone(true).appendTo(host);
          that._templateAttr(entryClone, 'dt-column', this.index());
          that._templateAttr(entryClone, 'dtcv-dataSrc', this.dataSrc());
          that._templateHtml(entryClone, 'dtcv-title', this.title());
        });
      });
      this.dom.template;
      return cloned;
    }
    /**
     * When a row is to be displayed, we need to create the card and display it.
     *
     * @param row The DataTables API instance for the row being rendered
     */
    _renderCard(row) {
      let dt = this.s.dt;
      let ctxData = dt.settings()[0].data;
      let idx = row.index();
      let card;
      // Can't do anything if the row doesn't exist! Unlikely, but possible
      if (!ctxData[idx]) {
        return;
      }
      if (ctxData[idx]._card) {
        // Reuse an existing card if we can
        card = ctxData[idx]._card;
      }
      else {
        let template = this._templatePrep();
        card = template.clone(true);
        this._cardData(row, card);
        // Row attribute
        this._templateAttr(card, 'dt-row', row.index());
        // Selection handling (select is optional)
        if (row.selected && row.selected()) {
          card.classAdd(this.classes.selected);
        }
        ctxData[idx]._card = card;
      }
      // Display the card
      this.dom.container.append(card);
    }
    _updateCard(rowIdx) {
      let dt = this.s.dt;
      let ctxData = dt.settings()[0].data;
      // No row data or card, do nothing
      if (!ctxData[rowIdx] || !ctxData[rowIdx]._card) {
        return;
      }
      let card = ctxData[rowIdx]._card;
      let row = dt.row(rowIdx);
      this._cardData(row, card);
    }
    _cardData(row, card) {
      // Find the display data points (i.e. the equivalent of a cell in the
      // host DataTable) and insert the values.
      this._templateHtml(card, 'dtcv-dataSrc', (dataSrc, colIdx) => {
        // If we've got a column index, then we can use the column rendering
        // function for display
        if (colIdx !== null) {
          return row.cell(row.index(), colIdx).render(this.c.orthogonal);
        }
        // Otherwise we read directly from the data source
        return dataSrc !== null ? util.data.get(dataSrc)(row.data()) : '';
      });
    }
  }
  /** Class names used by CardView for customisation */
  CardView.classes = {
    card: 'dtcv-card',
    cardContent: '',
    container: 'dtcv-container',
    data: 'dtcv-card_data',
    selectable: 'dtcv-container_selectable',
    selector: 'dtcv-card_selector',
    selected: 'dtcv-card_selected',
    shown: 'dt-cardview',
    title: 'dtcv-card_title'
  };
  /** Defaults */
  CardView.defaults = {
    breakpoints: [
      1200, // huge
      992, // large
      768, // medium
      576, // small
      0 // tiny
    ],
    columns: '*',
    gridColumns: {
      huge: 5,
      large: 4,
      medium: 3,
      small: 2,
      tiny: 1
    },
    mode: 'auto',
    orthogonal: 'display',
    pageLength: 'fit',
    responsiveBreakpoint: 'medium',
    template: dlList
  };
  /** CardView version */
  CardView.version = '1.0.1';
  CardView.templates = {
    dlList,
    miniTable,
    ulList
  };
  /** SVG icons that can be used by the content plugins */
  CardView.icons = icons;

  // Doesn't do anything - Not documented
  Api.register('cardView()', function () {
    return this.inst(this.context);
  });
  // Get the display state
  Api.register('cardView().displayed()', function () {
    let ctx = this.context[0];
    return ctx._cardView ? ctx._cardView.displayed() : false;
  });
  // Set a mode
  Api.register('cardView().mode()', function (mode) {
    let ctx = this.context[0];
    if (!mode) {
      return ctx._cardView ? ctx._cardView.mode() : null;
    }
    if (ctx._cardView) {
      ctx._cardView.mode(mode);
    }
    return this;
  });
  DataTable.ext.buttons.cardViewToggle = {
    action: function (e, dt, button, config) {
      let ctx = dt.settings()[0];
      if (ctx._cardView) {
        ctx._cardView.mode(ctx._cardView.displayed() ? 'table' : 'cards');
      }
      this.text(DataTable.ext.buttons.cardViewToggle.text(dt, button));
    },
    text: function (dt) {
      let ctx = dt.settings()[0];
      return !ctx._cardView || !ctx._cardView.displayed()
        ? dt.i18n('buttons.cardView', 'View cards')
        : dt.i18n('buttons.tableView', 'View table');
    }
  };
  DataTable.ext.buttons.cardView = {
    action: function (e, dt, button, config) {
      let ctx = dt.settings()[0];
      if (ctx._cardView) {
        ctx._cardView.mode('cards');
      }
    },
    init: function (dt, button) {
      let ctx = dt.settings()[0];
      let active = () => {
        this.active(ctx._cardView && ctx._cardView.displayed());
      };
      active();
      dt.on('cardView-display', active);
    },
    text: function (dt) {
      return dt.i18n('buttons.cardView', 'View cards');
    }
  };
  DataTable.ext.buttons.tableView = {
    action: function (e, dt, button, config) {
      let ctx = dt.settings()[0];
      if (ctx._cardView) {
        ctx._cardView.mode('table');
      }
    },
    init: function (dt, button) {
      let ctx = dt.settings()[0];
      let active = () => {
        this.active(!ctx._cardView || !ctx._cardView.displayed());
      };
      active();
      dt.on('cardView-display', active);
    },
    text: function (dt) {
      return dt.i18n('buttons.tableView', 'View table');
    }
  };
  DataTable.ext.buttons.autoView = {
    action: function (e, dt, button, config) {
      let ctx = dt.settings()[0];
      if (ctx._cardView) {
        ctx._cardView.mode('auto');
      }
    },
    init: function (dt, button) {
      let ctx = dt.settings()[0];
      let active = () => {
        this.active(!ctx._cardView || ctx._cardView.mode() === 'auto');
      };
      active();
      dt.on('cardView-mode', active);
    },
    text: function (dt) {
      return dt.i18n('buttons.tableView', 'Auto view');
    }
  };
  // Attach a listener to the document which listens for DataTables initialisation
  // events so we can automatically initialise
  Dom.s(document).on('preInit.dt.cardView', function (e, settings) {
    if (e.namespace !== 'dt') {
      return;
    }
    let init = settings.init.cardView;
    let defaults = DataTable.defaults.cardView;
    if (init || defaults) {
      let opts = {};
      if (util.is.plainObject(defaults)) {
        util.object.assign(opts, defaults);
      }
      if (util.is.plainObject(init)) {
        util.object.assign(opts, init);
      }
      if (init !== false) {
        new CardView(settings, opts);
      }
    }
  });
  // Alias for access
  DataTable.CardView = CardView;


  return DataTable;
}));
