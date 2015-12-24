
$(function () {
    'use strict'

    var filters = [
            'screens', 'partials', 'data', 'forms', 'actions', 'custom', 'notes'
        ],
        active_filters = [],
        filter_active = false,
        max_width = 800,
        $filterables = $('.obj, .elem');

    $('a').on('click', function (e) {
        e.preventDefault();
    });

    function apply_filter(name) {
        if (filters.indexOf(name) < 0) return false;
        if (active_filters.indexOf(name) > -1) return true;
        active_filters.push(name);
        return process_filters();
    }

    function remove_filter(name) {
        if (filters.indexOf(name) < 0) return false;
        var index = active_filters.indexOf(name);
        if (index < 0) return true;
        active_filters.splice(index, 1);
        return process_filters();
    }

    function clear_filters() {
        active_filters = [];
        return process_filters();
    }

    function process_filters() {
        if (active_filters.length) {
            var $elems = $();

            if (active_filters.indexOf('data') > -1) {
                $elems = $elems.add('.elem-data');
            }
            if (active_filters.indexOf('forms') > -1) {
                $elems = $elems.add('.elem-form');
            }
            if (active_filters.indexOf('actions') > -1) {
                $elems = $elems.add('.elem-action');
            }
            if (active_filters.indexOf('custom') > -1) {
                $elems = $elems.add($('.action-result.custom')
                    .parents('.elem'));
            }
            if (active_filters.indexOf('notes') > -1) {
                $elems = $elems.add('.elem-notes');
            }

            var hasPartialFilter = 
                    active_filters.indexOf('partials') > -1,
                hasScreenFilter = 
                    active_filters.indexOf('screens') > -1;

            if (hasPartialFilter || hasScreenFilter) {
                var $_partialobjs = $('.obj-partial')
                        .parents('.obj-name')
                        .parents('.obj'),
                    $_reducedset = $('.obj');

                if (hasPartialFilter && hasScreenFilter) {
                    // don't reduce set
                } else if (hasPartialFilter) {
                    $_reducedset = $_partialobjs;
                } else {
                    $_reducedset = $_reducedset.not($_partialobjs);
                }

                if ($elems.length) {
                    // show filtered reduced set
                    $elems = $_reducedset.add(
                        $_reducedset.find($elems));

                } else {
                    // show all from reduced set
                    $elems = $_reducedset.add(
                        $_reducedset.find('.elem'));
                }

                if (hasPartialFilter) {
                    // show partial action results
                    $elems = $elems.add($('.obj-partial')
                    .parents('.elem'));
                }
            }
            $elems = $elems.add(
                $elems.parents('.obj')
            );
            if (active_filters.indexOf('screens') > -1) {

            }
            $elems.css('display', '');
            $filterables.not($elems).css('display', 'none');
        } else {
            // show all
            $filterables.css('display', '');
        }
        return true;
    }

    $('[data-type="checkbox"]').on('click', function (e) {
        if ('true' === $(this).attr('data-value')) {
            $(this).attr('data-value', 'false');
            remove_filter($(this).attr('data-name').trim());
        } else {
            $(this).attr('data-value', 'true');
            apply_filter($(this).attr('data-name').trim());
        }
    });

    $('[data-action="clear-checks"]').on('click', function (e) {
        var $cont = $(this).parents('[data-checks-container]');
        if (!$cont.length) {
            $cont = $(document);
        }
        $cont.find('[data-type="checkbox"]').attr('data-value', 'false');
        clear_filters();
    });

    $('[data-type="filters"]').on('click', function (e) {
        var tm = 300,
            $toolbar = $('.toolbar');
        if (parseInt($toolbar.css('marginRight'))) {
            $toolbar.finish();
            $toolbar.animate({
                'marginRight': '0'
            }, tm, function () {
                $toolbar.css('marginRight', '0');
            });
        } else {
            $toolbar.finish();
            $toolbar.animate({
                'marginRight': '-200px'
            }, tm, function () {
                $toolbar.css('marginRight', '');
            });
        }
    });

    function collapse_toggle(context) {
        var tm = 300,
            $ref = $(context),
            $collapsible = $ref.parent().find('[data-collapsible]');
        if ($collapsible.length) {
            if ('true' === $collapsible.attr('data-collapsed')) {
                $collapsible.finish();
                if ($collapsible.attr('data-open-height')) {
                    $collapsible.animate({
                        'height': $collapsible.attr('data-open-height')
                    }, tm, function () {
                        $collapsible.css('height', '');
                        $collapsible.attr('data-collapsed', 'false');
                        $ref.attr('data-collapsed', 'false');
                        $collapsible.attr('data-open-height', $collapsible.height());
                    });
                } else {
                    $collapsible.css('height', '');
                    $collapsible.attr('data-collapsed', 'false');
                    $ref.attr('data-collapsed', 'false');
                    $collapsible.attr('data-open-height', $collapsible.height());
                }
            } else {
                $collapsible.finish();
                $collapsible.animate({
                    'height': '0'
                }, tm, function () {
                    $collapsible.css('height', '0');
                    $collapsible.attr('data-collapsed', 'true');
                    $ref.attr('data-collapsed', 'true');
                });
            }
        }
    }

    $('[data-collapse-toggle]').on('click', function (e) {
        collapse_toggle(this);
    });

    function expand_all() {
        $(document)
            .find('[data-collapse-toggle]')
            .attr('data-collapsed', 'false')
            .end()
            .find('[data-collapsible]')
            .css('height', '')
            .attr('data-collapsed', 'false')
            .each(function () {
                $(this).attr('data-open-height', $(this).height());
            });
    }

    function collapse_all() {
        $(document)
            .find('[data-collapse-toggle]')
            .attr('data-collapsed', 'true')
            .end()
            .find('[data-collapsible]')
            .css('height', '0')
            .attr('data-collapsed', 'true');
    }

    $('[data-name="expand-all"]').on('click', function (e) {
        expand_all();
    });

    $('[data-name="collapse-all"]').on('click', function (e) {
        collapse_all();
    });

    $('.project-body').find('.obj').each(function () {
        var min_width = 0
        var $elems = $(this).find('.elem');
        $elems.each(function () {
            var $action_name = $(this).find('.action-name'),
                curr_width = 0;
            if ($action_name.length) {
                curr_width = $action_name.width();
            } else {
                curr_width = $(this).width();
            }
            
            if (curr_width > min_width) {
                min_width = curr_width;
            }
        });
        if (min_width) {
            min_width += 10;
            var $action_elems = $elems.find('.action-name');
            $action_elems.css('min-width', Math.min(max_width, min_width));
            $elems.not($action_elems.parents('.elem'))
                .css('min-width', Math.min(max_width, min_width));
        }
    });

    // finally
    expand_all();
});