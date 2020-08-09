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
        const html = this.wikipageToHtml(data.page.content);
        const withTitle = `<span class='gomden-title-page-name'>Viewing page:${data.page.pagename}</span><br><br>` + html;
        $("#gomden-container").html(withTitle);
    };

    escapeHtml(text) {
        return $("<div>").text(text).html();
    }

    applyHeaders(escaped) {
        //var regexp = new RegExp(something, 'ig');
        //str.replace(regexp, '<span class="marked">$&</span>')
        return escaped.replace(/^# (.*)$/mg, "<h1 class='gomden-header'># $1</h1>")
            .replace(/^## (.*)$/mg, "<h2 class='gomden-header'>## $1</h2>")
            .replace(/^### (.*)$/mg, "<h3 class='gomden-header'>### $1</h3>")
            .replace(/^#### (.*)$/mg, "<h4 class='gomden-header'>#### $1</h4>")
    }

    applyLinks(withHeaders) {
        return withHeaders.replace(/page:([0-9a-z-]{3,100})/mg, `<a href='${this.config.viewPageUrl}$1'>page:$1</a>`)
    }

    wikipageToHtml(content) {
        const escaped = this.escapeHtml(content);
        const withHeaders = this.applyHeaders(escaped);
        const withLinks = this.applyLinks(withHeaders);
        return withLinks.replace(/\n/g, "<br />");
    }

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

    // Yes, this is janky
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
