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
var troopspead = {"spear":18,"sword":22,"axe":18,"archer":18,"spy":9,"light":10,"marcher":10,"heavy":11,"ram":30,"catapult":30,"snob":35};

$(function(){

    var storage = localStorage;
    var storagePrefix="Timer_";

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

    storageSet("troops",storageGet("troops",JSON.stringify({"current":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":1,"catapult":0,"snob":0},
                                                            "leer":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":0,"catapult":0,"snob":0}})));
    //storageSet("troops",JSON.stringify({"current":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":1,"catapult":0,"snob":0},
    //                                        "leer":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":0,"catapult":0,"snob":0}}));

    storageSet("current_template",storageGet("current_template","leer"));
    var troops	= JSON.parse(storageGet("troops"));
    if(troops[storageGet("current_template")]==undefined){
        storageSet("current_template","leer")
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
        .append($("<h3>").text("DS Timer"));


        var unitTable		= $("<table>").appendTo(settingsCell);

		var unitTableHead	= $("<tr>").attr("id","AF_unitTableHead").appendTo(unitTable);
		var unitTableInput	= $("<tr>").attr("id","AF_unitTableInput").appendTo(unitTable);
		for(var name in troopspead){
			$("<th>")
			.append(
				$("<span>")
				.append(
					$("<img>").attr("src","https://dsde.innogamescdn.com/8.40.2/27945/graphic/unit/unit_"+name+".png")
				)
			)
			.attr("id","AF_unitTableHead_"+name)
			.appendTo(unitTableHead);

			$("<td>")
			.append(
				$("<span>")
				.append(
					$("<input>")
					.attr("type","text")
					.attr("size","5")
					.attr("id",name)
					.on("input",function(){
						var thisname = $(this).attr("id");

						//troops[$("option:selected",select_template).val()][thisname]	= $(this).val()>0 ? parseInt($(this).val()) : 0;
                        troops.current[thisname]	= $(this).val()>0 ? parseInt($(this).val()) : 0;
						storageSet("troops",JSON.stringify(troops));
                        if(storageGet("current_template")!="---"){
                            $("<option>")
                            .appendTo($("#select_template"))
                            .val("---")
                            .text("---")
                            $("option",$("#select_template")).each(function(){
                                $(this).prop("selected",false);
                            })
                            storageSet("current_template","---")
                            $('option[value="'+storageGet("current_template")+'"]',$("#select_template")).eq(0).prop('selected', true);
                        }
						console.log(storageGet("troops"));
					})
				)
			)
			.attr("id","AF_unitTableInput_"+name)
			.appendTo(unitTableInput);
		}
        addRow2(unitTable,"unit-Table-row")

        var button_store_new_template = $("<button>")
        .attr("id","btn_store_new_template")
        .click(function(){
            troops[input_name_template.val()] = {};
            troops[input_name_template.val()] = JSON.parse(JSON.stringify(troops.current));
            $("<option>")
            .text(input_name_template.val())
            .attr("value",input_name_template.val())
            .appendTo(select_template);
            $("option",$("#select_template")).each(function(){
                $(this).prop("selected",false);
            })
            storageSet("troops",JSON.stringify(troops));
            storageSet("current_template",input_name_template.val())
            $('option[value="'+storageGet("current_template")+'"]',$("#select_template")).eq(0).prop('selected', true);
            console.log(storageGet("troops"));
            console.log(storageGet("current_template"))
        })
        .text("Als neue Vorlage speichern")
        .attr("class","btn")

        var button_store_template = $("<button>")
        .attr("id","btn_store_template")
        .click(function(){

            storageSet("troops",troops)
            console.log(storageGet("troops"));
        })
        .text("Vorlage Überschreiben")
        .attr("class","btn")

        var input_name_template = $("<input>")
        .attr("type","text")
        .attr("id","input_name_template")
        .val("Name")




        var select_template = $("<select>")
        //.append($("<option>").text("Neue Vorlage").attr("value","new"))
        .attr("id","select_template")
        .change(function(){
            storageSet("current_template", $("option:selected",select_template).val());
            fillTroops();
            $('option[value="---"]',$(this)).remove();
            console.log("current template: "+storageGet("current_template"));
        });
        for(var template_name in troops){
            if(template_name!="current"){
                $("<option>")
                .text(template_name)
                .attr("value",template_name)
                .appendTo(select_template)
                //.attr("id","opt_"+template_name)
                console.log(template_name+" "+storageGet("current_template"));
            }
        }



        var button_export       = $("<button>")
        .attr("id","btn_export")
        .click(function(){
            createExportString();
        })
        .text("Exportieren")
        .attr("class","btn")
        var curtime = timestrings();
        var input_time = $("<input>")
        .attr("type","datetime-local")
        .attr("step","0.25")
        .attr("id","export_time")
        .val(curtime.date[2]+"-"+curtime.date[1]+"-"+curtime.date[0]+"T"+curtime.time[0]  +":"+curtime.time[1]+":"+curtime.time[2]+".000")

        addRow(select_template,button_store_template)
        addRow(input_name_template,button_store_new_template);
        addRow(input_time,button_export);

        $('option[value="'+storageGet("current_template")+'"]',$("#select_template")).eq(0).prop('selected', true);

        fillTroops();

        function fillTroops(){
            for(var name in troopspead){
                $("input#"+name).val(troops[$("option:selected",select_template).val()][name]);
            }
            troops.current = JSON.parse(JSON.stringify(troops[storageGet("current_template")]));
        }
        function addRow(desc,content) {
            $("<tr>")
                .append($("<td>").append(desc))
                .append($("<td>").append(content))
                .appendTo(settingsTable);
        }
        function addRow2(obj,id){
            $("<tr>")
                .append($("<td>").append(obj))
                .attr("id",id)
                .appendTo(settingsTable);
        }
    }

    function createExportString(){
        var ex_str              = {}

        ex_str.own_id           = getPageAttribute("village");

        ex_str.own_coord        = {};
        var coord_string        = game_data.village.coord.split("|");
        ex_str.own_coord.x      = coord_string[0];
        ex_str.own_coord.y      = coord_string[1];

        ex_str.target_id        = $("a",$(".village_anchor").first()).first().attr("href")
        ex_str.target_id        = ex_str.target_id.substring(ex_str.target_id.indexOf("id=")+3,ex_str.target_id.length);

        ex_str.target_coord     = {};
        coord_string            = $("a",$(".village_anchor").first()).first().text();
        coord_string            = coord_string.substring(coord_string.lastIndexOf("(")+1,coord_string.lastIndexOf(")"));
        ex_str.target_coord.x   = coord_string.split("|")[0];
        ex_str.target_coord.y   = coord_string.split("|")[1];

        ex_str.attack_time      = {};
        datetime                = $("#export_time").val().split("T");
        var date                = datetime[0].split("-");
        var time                = datetime[1].split(":");
        time[3]                 = time[2].split(".")[1];
        time[2]                 = time[2].split(".")[0];
        ex_str.attack_time.time = time;
        ex_str.attack_time.date = date;

        alert(JSON.stringify(ex_str));
        console.log(JSON.stringify(ex_str));
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
