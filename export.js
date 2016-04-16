// ==UserScript==
// @name        DS_Timer_Export
// @namespace   de.die-staemme
// @version     0.1
// @description Export your Attack-Details fpr DS_Timer
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       unsafeWindow
// @match       https://*.die-staemme.de/game.php?*screen=place&try=confirm*
// @include     https://*.die-staemme.de/game.php?*screen=place&try=confirm*
// @copyright   2016+, Raznarek, stabel
// ==/UserScript==

var $ = typeof unsafeWindow != 'undefined' ? unsafeWindow.$ : window.$;

$(function(){

    var storage = localStorage;
    var storagePrefix="GM_";

    //Speicherfunktionen
    function storageGet(key,defaultValue) {
        var value= storage.getItem(storagePrefix+key);
        return (value === undefined || value === null) ? defaultValue : value;
        //return GM_getValue(key,defaultValue);
    }
    function storageSet(key,val) {
        storage.setItem(storagePrefix+key,val);
        //GM_setValue(key,val);
    }

    initUI();
    function initUI(){
        //var div_linkContainer = $("#linkContainer");
        var command_data_form   = $("#command-data-form");
        var contentContainer    = $("#contentContainer");
        var settingsRow         = $("<tr>").prependTo(contentContainer);
        var settingsCell        = $("<td>").appendTo(settingsRow);

        var settingsTable       = $("<table>")
        .attr("class","content-border")
        .attr("width","100%")
        .appendTo(settingsCell)
        //.append($("<tbody>"))
        .append($("<h3>").text("DS Timer"));

        var button_export       = $("<button>")
        .attr("id","btn_export")
        .click(function(){
            alert(input_time.val());
        })
        .text("Exportieren")
        .attr("class","btn")
        var curtime = timestrings();
        var input_time = $("<input>")
        .attr("type","datetime-local")
        .attr("step","0.25")
        .val(curtime.date[2]+"-"+curtime.date[1]+"-"+curtime.date[0]+"T"+curtime.time[0]  +":"+curtime.time[1]+":"+curtime.time[2]+".000")

        addRow(input_time,button_export);
        function addRow(desc,content) {
            $("<tr>")
                .append($("<td>").append(desc))
                .append($("<td>").append(content))
                .appendTo(settingsTable);
        }
    }
    function createExportString(){
        var own_id = getPageAttribute("village");
        var own_coord = {};
        var coord_string = game_data.village.coord.split("|");
        own_koords.x = coord_string[0];
        own_koords.y = coord_string[1];
    }
    function timestrings(){
        var dates	= $("#serverDate").text().split("/");
		var times 	= $("#serverTime").text().split(":");
        for(var i = 0; i<dates.length;i++){
            if(dates[i].length<2){
                dates[i] = "0"+dates[i];
            }
            if(times[i].length<2){
                times[i] = "0"+times[i];
            }
        }
        var datetime = {};
        datetime.time=times;
        datetime.date=dates;
        return datetime;

    }
    function currentTime(){
		var date 	= $("#serverDate").text().split("/");
		var time 	= $("#serverTime").text().split(":");
		var d		= new Date(
						parseInt(date[2]),
						parseInt(date[1]),
						parseInt(date[0]),
						parseInt(time[0]),
						parseInt(time[1]),
						parseInt(time[2]),
						0);
		return d;
	}
    function getPageAttribute(attribute){
        var params = document.location.search;
        var value = params.substring(params.indexOf(attribute+"=")+attribute.length+1,params.indexOf("&",params.indexOf(attribute+"=")) != -1 ? params.indexOf("&",params.indexOf(attribute+"=")) : params.length);
        return params.indexOf(attribute+"=")!=-1 ? value : "0";
    }
});
