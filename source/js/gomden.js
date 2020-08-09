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
        const THIS = this;

        $.get(url)
            .success(function(data) {
                THIS.loadPageSuccess(data);
            })
            .fail(function() {
                console.error("loadPage failed");
            });
    }

    loadPageSuccess(data) {
        console.log(data);

        $("#gomden-container").text(data.page.content);
    };
}