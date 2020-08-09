"use strict";

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var DEFAULT_GOMDEN_CONFIG = {};

var Gomden = function () {
    function Gomden(config) {
        _classCallCheck(this, Gomden);

        if (!config) {
            config = {};
        }
        this.config = $.extend({}, DEFAULT_GOMDEN_CONFIG, config);
    }

    _createClass(Gomden, [{
        key: "launch",
        value: function launch() {
            this.loadPage();
        }
    }, {
        key: "loadPage",
        value: function loadPage() {
            var url = this.config.getPageUrl;
            var THIS = this;

            $.get(url).success(function (data) {
                THIS.loadPageSuccess(data);
            }).fail(function (data) {
                THIS.loadPageFailure(data);
            });
        }
    }, {
        key: "loadPageFailure",
        value: function loadPageFailure(data) {
            var html = "\n            <span class='gomden-title-page-name'>Missing page:" + this.config.pageName + "</span><br><br>\n            <h1># This page does not exist</h1><br>\n            Click the edit button (above) to create this page.\n            ";
            $("#gomden-container").html(html);
        }
    }, {
        key: "loadPageSuccess",
        value: function loadPageSuccess(data) {
            console.log(data);
            var html = this.wikipageToHtml(data.page.content);
            var withTitle = "<span class='gomden-title-page-name'>Viewing page:" + data.page.pagename + "</span><br><br>" + html;
            $("#gomden-container").html(withTitle);
        }
    }, {
        key: "escapeHtml",
        value: function escapeHtml(text) {
            return $("<div>").text(text).html();
        }
    }, {
        key: "applyHeaders",
        value: function applyHeaders(escaped) {
            return escaped.replace(/^# (.*)$/mg, "<h1 class='gomden-header'># $1</h1>").replace(/^## (.*)$/mg, "<h2 class='gomden-header'>## $1</h2>").replace(/^### (.*)$/mg, "<h3 class='gomden-header'>### $1</h3>").replace(/^#### (.*)$/mg, "<h4 class='gomden-header'>#### $1</h4>");
        }
    }, {
        key: "applyLinks",
        value: function applyLinks(withHeaders) {
            return withHeaders.replace(/page:([0-9a-z-]{3,100})/mg, "<a href='" + this.config.viewPageUrl + "$1'>page:$1</a>");
        }
    }, {
        key: "wikipageToHtml",
        value: function wikipageToHtml(content) {
            var escaped = this.escapeHtml(content);
            var withHeaders = this.applyHeaders(escaped);
            var withLinks = this.applyLinks(withHeaders);
            return withLinks.replace(/\n/g, "<br />");
        }
    }, {
        key: "launchEdit",
        value: function launchEdit() {
            this.loadEditPage();
        }
    }, {
        key: "loadEditPage",
        value: function loadEditPage() {
            var url = this.config.getPageUrl;
            var THIS = this;

            $.get(url).success(function (data) {
                THIS.loadEditPageSuccess(data);
            }).fail(function (data) {
                THIS.loadEditPageFailure(data);
            });
        }

        // Yes, this is janky

    }, {
        key: "loadEditPageSuccess",
        value: function loadEditPageSuccess(data) {
            $("#gomden-container").html("\n            <form action=\"" + this.config.savePageUrl + "\" method=\"post\">\n            <textarea id=\"gomden-editor\" name=\"textedit\" rows=\"15\" style=\"width: 100%\"></textarea>\n            <button class=\"btn btn-primary\" type=\"submit\">Save</button>\n            <input type=\"hidden\" name=\"csrf_token\" value=\"" + CSRF_TOKEN + "\"/>\n            </form>\n        ");
            $("#gomden-editor").val(data.page.content);
        }

        // Yes, this is janky

    }, {
        key: "loadEditPageFailure",
        value: function loadEditPageFailure(data) {
            $("#gomden-container").html("\n            <form action=\"" + this.config.savePageUrl + "\" method=\"post\">\n            <textarea id=\"gomden-editor\" name=\"textedit\" rows=\"15\" style=\"width: 100%\"></textarea>\n            <button class=\"btn btn-primary\" type=\"submit\">Save</button>\n            <input type=\"hidden\" name=\"csrf_token\" value=\"" + CSRF_TOKEN + "\"/>\n            </form>\n        ");
            var content = "# This page does not exist\nClick the edit button (above) to create this page.\n";
            $("#gomden-editor").val(content);
        }
    }]);

    return Gomden;
}();