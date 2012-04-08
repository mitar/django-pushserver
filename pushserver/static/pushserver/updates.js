var _super = $.ajaxSettings.xhr;
$.ajaxSetup({
    xhr: function() {
        var xhr = _super();
        var getAllResponseHeaders = xhr.getAllResponseHeaders;

        xhr.getAllResponseHeaders = function() {
            var allHeaders = getAllResponseHeaders.call(xhr);
            if(allHeaders) {
                return allHeaders;
            }
            allHeaders = "";
            $(["Cache-Control", "Content-Language", "Content-Type", "Expires", "Last-Modified", "Pragma"]).each(function(i, header_name) {
                if(xhr.getResponseHeader(header_name)) {
                    allHeaders += header_name + ": " + xhr.getResponseHeader( header_name ) + "\n";
                }
            });
            return allHeaders;
        };
        return xhr;
    }
});

var updatesProcessors = {};

function registerUpdatesProcessor(type, processor) {
    if (updatesProcessors[type]) {
        updatesProcessors[type].push(processor);
    }
    else {
        updatesProcessors[type] = [processor];
    }
}

function processUpdate(data) {
    processors = updatesProcessors[data.type];
    if (processors) {
        jQuery.each(processors, function (i, processor) {
            processor(data);
        });
    }
}

function listenForUpdates() {
    function listen(last_modified, etag) {
        function delayedListen(new_last_modified, new_etag) {
            setTimeout(function () {
                listen(new_last_modified || last_modified, new_etag || '0');
            }, 1000); // 1 second delay
        }

        function warn(message) {
            if ((typeof window.console != "undefined") && (typeof window.console.warn == "function")) {
                window.console.warn(message);
            }
        }

        jQuery.ajax({
            'beforeSend': function (jqXHR) {
                jqXHR.setRequestHeader("If-None-Match", etag);
                jqXHR.setRequestHeader("If-Modified-Since", last_modified);
            },
            'url': updates_url,
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
                    processUpdate(data);
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

jQuery(document).ready(function () {
    listenForUpdates();
});
