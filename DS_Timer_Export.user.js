// ==UserScript==
// @name        DS_Timer_Export
// @namespace   de.die-staemme
// @version     0.1.5
// @description Export your Attack-Details for DS_Timer
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       unsafeWindow
// @match       https://*.die-staemme.de/game.php?*screen=place&try=confirm*
// @include     https://*.die-staemme.de/game.php?*screen=place&try=confirm*
// @copyright   2016+, Raznarek, stabel
// ==/UserScript==

var $ = typeof unsafeWindow != 'undefined' ? unsafeWindow.$ : window.$;
var troopspead = {"spear":18,"sword":22,"axe":18,"archer":18,"spy":9,"light":10,"marcher":10,"heavy":11,"ram":30,"catapult":30,"knight":10,"snob":35};

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

    /*storageSet("troops",storageGet("troops",JSON.stringify({"current":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":1,"catapult":0,"snob":0},
                                                            "leer":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":0,"catapult":0,"snob":0}})));*/
    storageSet("troops",storageGet("troops",JSON.stringify({"use_selected": {}, "current":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":1,"catapult":0,"snob":0},"leer":{}})));
    //storageSet("troops",JSON.stringify({"current":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":1,"catapult":0,"snob":0},"leer":{}}));
    //storageSet("troops",JSON.stringify({"current":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":1,"catapult":0,"snob":0},
    //                                        "leer":{"spear":0,"sword":0,"axe":0,"archer":0,"spy":0,"light":0,"marcher":0,"heavy":0,"ram":0,"catapult":0,"snob":0}}));

    storageSet("current_template",storageGet("current_template","leer"));
    storageSet("exported_data",storageGet("exported_data",JSON.stringify({})));
    storageSet("toogle_arriv_depart",storageGet("toogle_arriv_depart","arriv"));

    var exported_data = JSON.parse(storageGet("exported_data"));
    var troops	= JSON.parse(storageGet("troops"));
    if(troops[storageGet("current_template")]==undefined){
        storageSet("current_template","leer")
    }

    if(getPageAttribute("screen")=="place"){
        initUI_place();
    }else if(getPageAttribute("screen")=="settings" && getPageAttribute("mode")=="settings"){
        //initUI_settings();
    }

    var btn_settings = $("<button>").appendTo($("#linkContainer"))
    .click(function(){
        initUI_settings();
    })
    .text("DSTIMER")
    .attr("class","btn")

    function initUI_settings(){
        //Seiteninhalt entfernen, damit Einstellungsseite aufgebaut werden kann
        var contentContainer   = $("#contentContainer");
        $("tbody",contentContainer).first().remove();

        //Aufbau neuer Seiteninhalt
        var settingsRow         = $("<tr>")
            .appendTo(contentContainer);
        var settingsCell        = $("<td>")
            .appendTo(settingsRow);
        var settingsTable       = $("<table>")
            .attr("class","content-border")
            .attr("width","100%")
            .appendTo(settingsCell)
            .append($("<h3>").text("DS Timer - Einstellungen"));

        var exportsRow         = $("<tr>")
            .appendTo(contentContainer);
        var exportsCell        = $("<td>")
            .appendTo(exportsRow);
        var exportsTable       = $("<table>")
            .attr("class","content-border")
            .attr("width","100%")
            .attr("id","exportsTable")
            .appendTo(exportsCell)
            .append($("<h3>").text("DS Timer - exportierte Daten"));

        var exported_data_Table		= $("<table>").appendTo(exportsCell);

    	var exported_data_Table_Head	= $("<tr>").attr("id","exported_data_Table_Head").appendTo(exported_data_Table);

        function addExportedDataRow(data){
            $("<tr>")
                .appendTo(exported_data_Table)

        }
    }

    function initUI_place(){
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
        //storageSet("troops",JSON.stringify(troops));

		for(var name in troopspead){
            $("<th>")
			.append(
				$("<span>")
				.append(
					$("<img>").attr("src","https://dsde.innogamescdn.com/asset/e9773236/graphic/unit/unit_"+name+".png")
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
                        troops.current[thisname]	= $(this).val()!="0" && $(this).val()!="" ? $(this).val() : "";//undefined;
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
                if(input_name_template.val()=="current" || input_name_template.val()=="leer"){
                    console.log("Ungültiger name!");
                    return;
                }
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
                $('option[value="---"]',$("#select_template")).remove();
                console.log(storageGet("troops"));
                console.log(storageGet("current_template"))
            })
            .text("Als neue Vorlage speichern")
            .attr("class","btn")

        var button_remove_template = $("<button>")
            .attr("id","btn_store_template")
            .click(function(){
                if(select_template.val()!="---" && select_template.val()!="leer"&& select_template.val()!="current"){
                    troops[select_template.val()]=undefined;
                    $('option[value="'+select_template.val()+'"]',$("#select_template")).remove();
                    storageSet("current_template","leer")
                    $('option[value="leer"]',$("#select_template")).eq(0).prop('selected', true);
                    storageSet("troops",JSON.stringify(troops));
                    fillTroops();
                }else{console.log("Diese Vorlage kann nicht gelöscht werden.")}
                console.log(storageGet("troops"));
            })
            .text("Vorlage Entfernen")
            .attr("class","btn")

        var input_name_template = $("<input>")
            .attr("type","text")
            .attr("id","input_name_template")
            .val("Neue Vorlage")




        var select_template = $("<select>")
        //.append($("<option>").text("Neue Vorlage").attr("value","new"))
            .attr("id","select_template")
            .change(function(){
                storageSet("current_template", $("option:selected",select_template).val());
                fillTroops();
                $('option[value="---"]',$(this)).remove();
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
                input_export.attr("type","");
                createExportString();
            })
            .text("Exportieren")
            .attr("class","btn")
        var input_export        = $("<input>")
            .attr("type","hidden")
            .attr("id","input_export")
            .val("")
        var curtime = timestrings();
        var input_time = $("<input>")
            .attr("type","datetime-local")
            .attr("step","0.25")
            .attr("id","export_time")
            .val(curtime.date[2]+"-"+curtime.date[1]+"-"+curtime.date[0]+"T"+curtime.time[0]  +":"+curtime.time[1]+":"+curtime.time[2]+".000");
        var label_arrival_departure =$("<span>")
            .click(function(){
                if(storageGet("toogle_arriv_depart")=="depart"){
                    label_arrival_departure.text("(Ankunftszeit)");
                    storageSet("toogle_arriv_depart","arriv");
                }else{
                    label_arrival_departure.text("(Abschickzeit)");
                    storageSet("toogle_arriv_depart","depart");
                }
            });
        var label_force =$("<span>")
            .text(" Truppen nicht prüfen? ");
        var checkbox_force = $("<input>")
            .prop("type","checkbox")
            .attr("id","checkforce")

        if(storageGet("toogle_arriv_depart")=="arriv"){
            label_arrival_departure.text("(Ankunftszeit)");
        }else{
            label_arrival_departure.text("(Abschickzeit)");
        }

        addRow(select_template,button_remove_template)
        addRow(input_name_template,button_store_new_template);
        addRow($("<span>").append(input_time).append(label_arrival_departure).append(label_force).append(checkbox_force),button_export);
        addRow2(input_export,"export");

        $('option[value="'+storageGet("current_template")+'"]',$("#select_template")).eq(0).prop('selected', true);

        fillTroops();
        //HIER wird der spaß überschrieben


        function fillTroops(){
            for(var name in troopspead){
                if($("option:selected",select_template).val() == "use_selected") {
                    $("input#"+name).val($(".units-row .unit-item.unit-item-"+name).text());
                } else if(troops[$("option:selected",select_template).val()][name]!=""){
                    $("input#"+name).val(troops[$("option:selected",select_template).val()][name]);
                }else{
                    $("input#"+name).val("0");
                }

            }
            if($("option:selected",select_template).val() == "use_selected") {
                for(var name_ in troopspead) {
                    troops.current[name_] = $(".units-row .unit-item.unit-item-"+name_).text();
                }
            } else {
                troops.current = JSON.parse(JSON.stringify(troops[storageGet("current_template")]));
            }
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
                .appendTo(settingsTable)

        }
    }

    function createExportString(){
        var ex_str              = {}

        ex_str.source_id        = parseInt(getPageAttribute("village"));

        ex_str.source_coord     = {};
        var coord_string        = game_data.village.coord.split("|");
        ex_str.source_coord.x   = parseInt(coord_string[0]);
        ex_str.source_coord.y   = parseInt(coord_string[1]);

        ex_str.target_id        = $("a",$(".village_anchor").first()).first().attr("href")
        ex_str.target_id        = parseInt(ex_str.target_id.substring(ex_str.target_id.indexOf("id=")+3,ex_str.target_id.length));

        ex_str.target_coord     = {};
        coord_string            = $("a",$(".village_anchor").first()).first().text();
        coord_string            = coord_string.substring(coord_string.lastIndexOf("(")+1,coord_string.lastIndexOf(")"));
        ex_str.target_coord.x   = parseInt(coord_string.split("|")[0]);
        ex_str.target_coord.y   = parseInt(coord_string.split("|")[1]);

        if(storageGet("toogle_arriv_depart")=="arriv"){
            ex_str.arrival_time     = $("#export_time").val();
        }else{
            ex_str.departure_time   = $("#export_time").val();
        }

        var type                = $('input[name="attack"]').val();
        ex_str.type             = type == "true" ? "attack" : "support";
        ex_str.units            = {};
        ex_str.units            = JSON.parse(JSON.stringify(troops.current));
        ex_str.force            = $("#checkforce").prop("checked");

        ex_str.domain           = location.host;
        ex_str.player           = game_data.player.name; // in UV gives player name not sitter name

        ex_str.vacation         = getPageAttribute("t");
        ex_str.sitter           = game_data.player.sitter;
        ex_str.player_id        = game_data.player.id;

        ex_str.building         = $("#place_confirm_catapult_target select[name=building] option:selected").val();


        console.log(JSON.stringify(ex_str));
        $("#input_export").val(JSON.stringify(ex_str));

        exported_data[Object.keys(exported_data).length] = ex_str;
        console.log(JSON.stringify(ex_str));
    }
    function timestrings(){
        var dates	= $("#serverDate").text().split("/");
        var times = $("#serverTime").text().split(":");
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
