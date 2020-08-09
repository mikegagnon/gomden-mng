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
            }).fail(function () {
                console.error("loadPage failed");
            });
        }
    }, {
        key: "loadPageSuccess",
        value: function loadPageSuccess(data) {
            console.log(data);
            var html = this.wikipageToHtml(data.page.content);
            $("#gomden-container").html(html);
        }
    }, {
        key: "escapeHtml",
        value: function escapeHtml(text) {
            return $("<div>").text(text).html();
        }
    }, {
        key: "applyHeaders",
        value: function applyHeaders(escaped) {
            //var regexp = new RegExp(something, 'ig');
            //str.replace(regexp, '<span class="marked">$&</span>')
            return escaped.replace(/^# (.*)$/mg, "<h1 class='gomden-header'># $1</h1>").replace(/^## (.*)$/mg, "<h2 class='gomden-header'>## $1</h2>").replace(/^### (.*)$/mg, "<h3 class='gomden-header'>### $1</h3>").replace(/^#### (.*)$/mg, "<h4 class='gomden-header'>#### $1</h4>");
        }
    }, {
        key: "wikipageToHtml",
        value: function wikipageToHtml(content) {
            var escaped = this.escapeHtml(content);
            var withHeaders = this.applyHeaders(escaped);
            return withHeaders.replace(/\n/g, "<br />");
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
            }).fail(function () {
                console.error("loadPage failed");
            });
        }

        // Yes, this is janky

    }, {
        key: "loadEditPageSuccess",
        value: function loadEditPageSuccess(data) {
            $("#gomden-container").html("\n            <form action=\"" + this.config.savePageUrl + "\" method=\"post\">\n            <textarea id=\"gomden-editor\" name=\"textedit\" rows=\"15\" style=\"width: 100%\"></textarea>\n            <button class=\"btn btn-primary\" type=\"submit\">Save</button>\n            <input type=\"hidden\" name=\"csrf_token\" value=\"" + CSRF_TOKEN + "\"/>\n            </form>\n        ");
            $("#gomden-editor").val(data.page.content);
        }
    }]);

    return Gomden;
}();