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
            .fail(function(data) {
                THIS.loadPageFailure(data);
            });
    }

    loadPageFailure(data) {
        const html = `
            <span class='gomden-title-page-name'>Missing page:${this.config.pageName}</span><br><br>
            <h1># This page does not exist</h1><br>
            Click the edit button (above) to create this page.
            `;
        $("#gomden-container").html(html);
    }

    loadPageSuccess(data) {
        console.log(data);
        const html = this.wikipageToHtml(data.page.content);
        const withTitle = `<span class='gomden-title-page-name'>Viewing page:${data.page.pagename}</span><br><br>` + html;
        $("#gomden-container").html(withTitle);
        $("#gomden-container .gomden-page-link").each(function(i, value) {
            const pagename = $(value).text().slice(5);
            if (!data.existingPagenames.includes(pagename)) {
                $(value).addClass("gomden-missing-page-link");
            }
        });
    };

    escapeHtml(text) {
        return $("<div>").text(text).html();
    }

    applyHeaders(escaped) {
        return escaped.replace(/^# (.*)$/mg, "<h1 class='gomden-header'># $1</h1>")
            .replace(/^## (.*)$/mg, "<h2 class='gomden-header'>## $1</h2>")
            .replace(/^### (.*)$/mg, "<h3 class='gomden-header'>### $1</h3>")
            .replace(/^#### (.*)$/mg, "<h4 class='gomden-header'>#### $1</h4>")
    }

    applyLinks(withExternalLinks) {
        return withExternalLinks.replace(/page:([0-9a-z-]{3,100})/mg, `<a class="gomden-page-link" href='${this.config.viewPageUrl}$1'>page:$1</a>`)
    }

    wikipageToHtml(content) {
        const escaped = this.escapeHtml(content);
        const withHeaders = this.applyHeaders(escaped);
        const withExternalLinks = this.applyExternalLinks(withHeaders);
        const withLinks = this.applyLinks(withExternalLinks);
        return withLinks.replace(/\n/g, "<br />");
    }

    // From: https://www.codespeedy.com/replace-url-with-clickable-link-javascript/
    applyExternalLinks(withHeaders) {
        const exp_match = /(\b(https?|):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
        return withHeaders.replace(exp_match, "<a href='$1'>$1</a>");
    }

    launchEdit() {
        if (this.config.allowEdit) {
            this.loadEditPage();
        } else {
            this.loadNoEditPage();
        }
    }

    loadNoEditPage() {
         $("#gomden-container").html(`
            <p><a class="gomden-page-link" href="${this.config.viewPageUrl}${this.config.pageName}">page:${this.config.pageName}</a> is owned by @${this.config.ownerUsername}, and has disabled other users from editing this page.</p>
        `);
    }

    loadEditPage() {
        const url = this.config.getPageUrl;
        const THIS = this;

        $.get(url)
            .success(function(data) {
                THIS.loadEditPageSuccess(data);
            })
            .fail(function(data) {
                THIS.loadEditPageFailure(data);
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

    // Yes, this is janky
    loadEditPageFailure(data) {
        $("#gomden-container").html(`
            <form action="${this.config.savePageUrl}" method="post">
            <textarea id="gomden-editor" name="textedit" rows="15" style="width: 100%"></textarea>
            <button class="btn btn-primary" type="submit">Save</button>
            <input type="hidden" name="csrf_token" value="${CSRF_TOKEN}"/>
            </form>
        `);
        const content = `# This page does not exist
Click the edit button (above) to create this page.
`;
        $("#gomden-editor").val(content);
    }

    launchPermissions() {
        let inside;

        if (this.config.userid === 0) {
            inside = `
                <p>You are not logged in. You may not change the permissions for this page.</p>
                <div>
                  <input type="checkbox" id="allowEdits" name="allowEdits" disabled>
                  <label for="allowEdits" class="gomden-disabled-text">Allow edits</label>
                </div>
                `;
        } else if (this.config.userid === this.config.ownerUserid) {
            inside = `
            <div>
              <input type="checkbox" id="allowEdits" name="allowEdits">
              <label for="allowEdits">Allow edits</label>
            </div>
            <button class="btn btn-primary" type="submit">Save permissions</button>
            <input type="hidden" name="csrf_token" value="${CSRF_TOKEN}"/>`;
        } else {
            inside = `
                <p>You are logged in as @${this.config.username}. You may not change the permissions for this page.</p>
                <div>
                  <input type="checkbox" id="allowEdits" name="allowEdits" disabled>
                  <label for="allowEdits" class="gomden-disabled-text">Allow edits</label>
                </div>
                `;
        }

        $("#gomden-container").html(`
            <form action="${this.config.savePermissionsUrl}" method="post">
            <p><a class="gomden-page-link" href="${this.config.viewPageUrl}${this.config.pageName}">page:${this.config.pageName}</a> is owned by @${this.config.ownerUsername}.</p>
            ${inside}
            </form>
        `);

        $("#allowEdits").prop("checked", this.config.allowEdits);
    }
}
