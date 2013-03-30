(function ($) {
    var subscribedChannels = {};
    var updatesProcessors = {};

    function warn(message) {
        if ((typeof window.console != 'undefined') && (typeof window.console.warn == 'function')) {
            window.console.warn(message);
        }
    }

    function processUpdate(channel_name, data) {
        if (!updatesProcessors[channel_name]) {
            return;
        }

        var processors = updatesProcessors[channel_name][data.type];
        if (processors) {
            $.each(processors, function (i, processor) {
                processor(data);
            });
        }
    }

    function listenForUpdates(channel_name, channel_url) {
        function listen(last_modified, etag) {
            function delayedListen(new_last_modified, new_etag) {
                setTimeout(function () {
                    listen(new_last_modified || last_modified, new_etag || '0');
                }, 1000); // 1 second delay
            }

            $.ajax({
                'beforeSend': function (jqXHR) {
                    jqXHR.setRequestHeader('If-None-Match', etag);
                    jqXHR.setRequestHeader('If-Modified-Since', last_modified);
                },
                'xhrFields': {
                    'withCredentials': true
                },
                'cache': false,
                'url': channel_url,
                'dataType': 'json',
                'type': 'GET',
                'timeout': 0,
                'success': function (data, textStatus, jqXHR) {
                    var new_last_modified = jqXHR.getResponseHeader('Last-Modified');
                    try {
                        var new_etag = jqXHR.getResponseHeader('Etag');
                        if (new_etag === null) throw null;
                    }
                    catch (e) {
                        try {
                            // Chrome and other WebKit-based browsers do not (yet) support access to Etag
                            // so we try to find the same information in the Cache-Control field
                            new_etag = (/etag=(\S+)/.exec(jqXHR.getResponseHeader('Cache-Control')))[1];
                        }
                        catch (e) {}
                    }

                    if (new_last_modified === null) {
                        warn("Last-Modified field is not available");
                    }
                    if (new_etag === null) {
                        warn("Etag field is not available");
                    }

                    if (!data) {
                        warn("No data in push request");
                    }
                    else {
                        processUpdate(channel_name, data);
                    }

                    if ((new_last_modified !== null) && (new_etag !== null)) {
                        listen(new_last_modified, new_etag);
                    }
                    else {
                        // TODO: Should we handle the error in some other manner?
                        delayedListen(new_last_modified, new_etag);
                    }
                },
                'error': function (jqXHR, textStatus, errorThrown) {
                    // TODO: Should we handle the error in some other manner?
                    delayedListen(last_modified, etag);
                }
            });
        }
        listen('Thu, 1 Jan 1970 00:00:00 GMT', '0');
    }

    $.updates = {};

    $.updates.subscribe = function (channels) {
         $.each(channels, function (name, url) {
            if (!subscribedChannels[name] && url) {
                subscribedChannels[name] = url;
                listenForUpdates(name, url);
            }
        });
    };

    $.updates.registerProcessor = function (channel_name, type, processor) {
        if (!updatesProcessors[channel_name]) {
            updatesProcessors[channel_name] = {};
        }

        if (!updatesProcessors[channel_name][type]) {
            updatesProcessors[channel_name][type] = [];
        }

        updatesProcessors[channel_name][type].push(processor);
    };

    // Workaround for Firefox bug, based on http://bugs.jquery.com/ticket/10338#comment:13
    var _super = $.ajaxSettings.xhr;

    $.ajaxSetup({
        'xhr': function() {
            var xhr = _super();
            var getAllResponseHeaders = xhr.getAllResponseHeaders;

            xhr.getAllResponseHeaders = function () {
                try {
                    var allHeaders = getAllResponseHeaders.call(xhr);
                    if (allHeaders) {
                        return allHeaders;
                    }
                }
                catch (e) {}

                allHeaders = '';
                $.each([
                    'Cache-Control',
                    'Content-Language',
                    'Content-Type',
                    'Expires',
                    'Last-Modified',
                    'Pragma',
                    'Etag'
                ], function (i, headerName) {
                    try {
                        var headerValue = xhr.getResponseHeader(headerName);
                        if (headerValue) {
                            allHeaders += headerName + ': ' + headerValue + '\n';
                        }
                    }
                    catch (e) {}
                });
                return allHeaders;
            };

            return xhr;
        }
    });

    var ajaxRequests = [];
    $(document).ajaxSend(function (event, jqXHR, ajaxOptions) {
        ajaxRequests.push(jqXHR);
    }).ajaxComplete(function (event, jqXHR, ajaxOptions) {
        ajaxRequests = $.grep(ajaxRequests, function (request, i) {
            return jqXHR !== request;
        });
    });

    // We have to manually abort all pending requests because otherwise an
    // Ajax error is triggered when browser closes the page which cannot be
    // distinguished from real Ajax errors
    // By aborting, you can check if Ajax error is "abort" and ignore it
    function ajaxUnload (event) {
        $.each(ajaxRequests, function(i, request) {
            request.abort();
        });
        ajaxRequests = [];
    }

    $(window).bind('beforeunload', ajaxUnload).bind('unload', ajaxUnload);
})(jQuery);
