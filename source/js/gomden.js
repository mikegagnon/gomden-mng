const DEFAULT_GOMDEN_CONFIG = {
};

class Gomden {

    constructor(config) {
        if (!config) {
            config = {}
        }
        this.config = $.extend({}, DEFAULT_GOMDEN_CONFIG, config);
    }

    launch() {
        this.loadPage();
    }

    loadPage() {
        const url = this.config.getPageUrl;

         $.get(url)
            .success(function(data) {
                console.log(data);
            })
            .fail(function() {
                console.error("loadPage failed");
            });
    }
}