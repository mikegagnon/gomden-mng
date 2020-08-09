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

    launchEdit() {
        this.loadEditPage();
    }

    loadEditPage() {
        const url = this.config.getPageUrl;
        const THIS = this;

        $.get(url)
            .success(function(data) {
                THIS.loadEditPageSuccess(data);
            })
            .fail(function() {
                console.error("loadPage failed");
            }); 
    }

    loadEditPageSuccess(data) {
        $("#gomden-container").html(`
            <form action="${this.config.savePageUrl}" method="post">
            <textarea id="gomden-editor" name="textedit" rows="15" style="width: 100%"></textarea>
            <button class="btn btn-primary" type="submit">Save</button>
            <input type="hidden" name="csrf_token" value="${CSRF_TOKEN}"/>
            </form>
        `);
        $("#gomden-editor").val(data.page.content);
    }
}
