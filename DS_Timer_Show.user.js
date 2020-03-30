// ==UserScript==
// @name        DS_Timer_Show
// @namespace   de.die-staemme
// @version     0.2.1
// @description Export your Attack-Details for DS_Timer
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       unsafeWindow
// @match       https://*.die-staemme.de/game.php?*screen=info_village*
// @match       https://*.die-staemme.de/game.php?*screen=overview*
// @copyright   2019+, Raznarek, stabel
// ==/UserScript==

var $ = typeof unsafeWindow != 'undefined' ? unsafeWindow.$ : window.$;

var unit_asset = "https://dsde.innogamescdn.com/asset/c6122a3/graphic/unit/unit_";
var units = ["spear", "sword", "axe", "archer", "spy", "light", "marcher", "heavy", "ram", "catapult", "knight", "snob"];

$(function(){
  var storage = localStorage;
  var storagePrefix="Timer_show_";
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
  function get_actions() {
    //console.log('127.0.0.1:5000/show/'+getDomain()+'/target_id/'+target_id)
    var page = getPageAttribute("screen");
    if (page == "info_village") {
      var id = getPageAttribute("id");
      var type = "target_id";
    } else if (page == "overview") {
      var id = getPageAttribute("village");
      var type = "source_id";
    } else if (page == "overview_villages") {
      var mode = $("td.selected", $("#overview_menu")).text();
      if (mode ==  "Befehle ") {
        var id = game_data.player.id;
        var type = "player_id";
      } else {
        return;
      }
    } else {
      return;
    }
    $.ajax({ url: 'http://127.0.0.1:5000/show/'+getDomain()+'/'+type+'/'+id,
      success: function(response){
        console.log(JSON.stringify(response));
        init_UI(response)
      }, error: function(response){
        console.log('server error');
      }
    })
  }
  get_actions();
  console.log("hey")
  //init_UI();
  function init_UI(response){
    console.log("init_UI")
    var page = getPageAttribute("screen");
    if (response.length == 0){ // Abbruch, wenn keine Angriffe geplant
      console.log("keine geplanten Angriffe")
      return
    }
    var current_attacks = [];
    // create table for outgoings
    if (page == "overview_villages") {
      if ($("#commands_table").length == 0) {
        var command_table = $("<table>").attr("id", "commands_table").attr("class", "vis overview_table")
        var command_table_header = $("<tr>").appendTo(command_table)
          .append($("<th>").text("Befehle ("+response.length+")"))
          .append($("<th>").text("Herkunftsdorf"))
          .append($("<th>").text("Ankunft"))
          .append($("<th>").append($("<img>").attr("src", unit_asset+"spear")))
        for (unit of units) {
          commands_table_header.append($("<th>").attr("style", "text-align:center").append($("<img>").attr("src", unit_asset+unit+".png")));
        }

      } else {
        var command_table = $("#commands_table");
        $(".row_ax").each(function(){
          var time_string = $("td:eq(2)", $(this)).text();
          var timestamp = unparseTime(time_string);
          $(this).attr("data-endtime", timestamp)
          current_attacks.push(timestamp)
        });
      }
    } else if (page == "overview" || page == "info_village") {
      if($("#commands_outgoings").length==0){
        var commands_outgoings = $("<div>")
          .attr("id", "commands_outgoings")
        var command_table = $("<table>").appendTo(commands_outgoings)
          .attr("id", "command_table")
          .attr("class", "vis").attr("style", "width:100%");
        var command_header = $("<tr>").appendTo(command_table)
          .append($("<th>").attr("width", "52%").html("Eigene Befehle"))
          .append($("<th>").attr("width", "33%").html("Ankunft"))
          .append($("<th>").attr("width", "15%").html("Ankunft in"));
        if (page == "info_village"){
          var note_table = $("#message").closest("table");
          commands_outgoings.insertAfter(note_table);
        } else if (page == "overview") {
          $("<div>").attr("id", "show_outgoing_units").attr("class", "vis moveable widget commands-container-outer")
            .append($("<h4>").attr("class", "head with-button ui-sortable-handle").text("Deine Truppen"))
            .append($("<div>").attr("id", "widget_content").attr("style", "display: block;"))
            .appendTo($("#leftcolumn"))
            .append(commands_outgoings)
        }
      } else {
        var command_table = $("#commands_outgoings").find("table").first();
        $(".command-row").each(function(){ //add data-endtime to command-row
          $(this).attr("data-endtime",$("span[data-endtime]", $(this)).data("endtime")+$("span[class='grey small']", $(this)).text());
          current_attacks.push(parseInt($(this).data("endtime")));
        });
      }
    }
    console.log(JSON.stringify(current_attacks))
    for (var action of response){ //create rows for schedules atts and insert according to existing atts
      var arrival_time = new Date(action["arrival_time"]);
      arrival_time.setMilliseconds(action["milliseconds"]);
      var arrival_timestamp = Date.parse(arrival_time);
      var mseconds = expandNumberString(action["milliseconds"],3)
      var arrival_time_string = parseTime(arrival_time);
      var position = -1;
      for (var i = 0; i< current_attacks.length; i++) {
        if (current_attacks[i] > arrival_timestamp){
          position = i;
          break;
        }
        if (i==current_attacks.length - 1){position = current_attacks.length}
      }
      current_attacks.splice(position == -1 ? 0: position, 0, arrival_timestamp);
      console.log(JSON.stringify(current_attacks))
      console.log("position: "+position)
      if (page=="overview_villages") {
        var new_command_row = $("<tr>").attr("class", "nowrap  selected  row_ax").attr("data-endtime", arrival_timestamp)
        var target_td = $("<td>").appendTo(new_command_row)
              .append($("<span>").append($("<img>").attr("src", "https://dsde.innogamescdn.com/asset/b8e610d/graphic/command/"+action["type"]+(action["type"] == "attack" ? "_"+action["size"] : "")+".png")))
        appendUnitSymbols(action["units"], target_td)
        target_td.append($("<a>").attr("href", "/game.php?village="+action["source_id"]+"&screen=info_village&id="+action["target_id"]).html(" "+action["target_village_name"]+" ("+action["target_coord"]["x"]+"|"+action["target_coord"]["y"]+")"))

        new_command_row.append(
            $("<td>")
              .append($("<a>").attr("href", "/game.php?village="+action["source_id"]+"&screen=overview").html(" "+action["source_village_name"]+" ("+action["source_coord"]["x"]+"|"+action["source_coord"]["y"]+")"))
          )
          .append($("<td>").html(arrival_time_string).append($("<span>").html(mseconds).attr("class", "grey small")));
        for (var unit of units){
          var troops = 0;
          if (unit in action["units"] && action["units"][unit] != "") {
            troops = action["units"][unit];
          }
          new_command_row.append($("<td>").attr("class", "unit-item"+(troops == 0 ? " hidden" : "")).html(troops))
        }
        if (position == -1){//keine bereits existierenden /eingetragenen Angriff
          new_command_row.appendTo(command_table);
        } else if(position == 0){
          new_command_row.insertBefore($(".row_ax").first());
        } else {
          new_command_row.insertAfter($(".row_ax[data-endtime ="+current_attacks[position-1]+"]"));
        }
      } else if (page == "overview" || page == "info_village") {
        var new_command_row = $("<tr>").attr("class", "command-row").attr("data-endtime", arrival_timestamp)
        if (page == "overview") {
          var target_td = $("<td>").appendTo(new_command_row) //+(action["type"] == "attack" ? "_"+action["size"] : "")
            .append($("<img>").attr("src", "https://dsde.innogamescdn.com/asset/b8e610d/graphic/command/"+action["type"]+(action["type"] == "attack" ? "_"+action["size"] : "")+".png"))
          appendUnitSymbols(action["units"], target_td)
          target_td.append($("<a>").attr("href", "/game.php?village="+action["source_id"]+"&screen=info_village&id="+action["target_id"]).html((action["type"] == "attack" ? " Angriff auf " : " Unterstützung für ")+action["source_village_name"]+" ("+action["target_coord"]["x"]+"|"+action["target_coord"]["y"]+")"))
        }else{
          var source_td = $("<td>").appendTo(new_command_row)
            .append($("<img>").attr("src", "https://dsde.innogamescdn.com/asset/b8e610d/graphic/command/"+action["type"]+(action["type"] == "attack" ? "_"+action["size"] : "")+".png"))
          appendUnitSymbols(action["units"], source_td)
          source_td.append($("<a>").attr("href", "/game.php?village="+action["source_id"]+"&screen=overview").html(" "+action["source_village_name"]))
        }
        new_command_row.append($("<td>").html(arrival_time_string).append($("<span>").html(mseconds).attr("class", "grey small")))
          .append($("<td>").append($("<span>").html(getTimeDiffAsString(arrival_timestamp)+"").attr("data-endtime", arrival_timestamp+"").attr("class", "countdown-span")));
        if (position == -1){//keine bereits existierenden /eingetragenen Angriff
          new_command_row.appendTo(command_table);
        } else if(position == 0){
          new_command_row.insertBefore($(".command-row").first());
        } else {
          new_command_row.insertAfter($(".command-row[data-endtime ="+current_attacks[position-1]+"]"));
        }
      }
    }
    var button_test = $("<button>").appendTo($("#linkContainer"))
      .click(function(){
        alert($("#abcabc").text())
      }).text("DSTIMER")
      .attr("class","btn")
      .attr("id","undso")
  }
  function getPageAttribute(attribute){
    var params = document.location.search;
    var value = params.substring(params.indexOf(attribute+"=")+attribute.length+1,params.indexOf("&",params.indexOf(attribute+"=")) != -1 ? params.indexOf("&",params.indexOf(attribute+"=")) : params.length);
    return params.indexOf(attribute+"=")!=-1 ? value : "0";
  }
  function getDomain(){
    return window.location.hostname;
  }
  function parseTime(at){
    // Date object to "heute um 22:43:54:442"; "morgen um 22:47:32:295"; am 19.03. um 15:03:32:295
    var ct = currentTime();
    at.setMinutes(at.getMinutes()+at.getTimezoneOffset()) // Sommer/Winterzeit
    var tm = new Date(ct.getFullYear(), ct.getMonth(), ct.getDate() + 1); // morgen
    var prefix = "";
    if(ct.getFullYear()==at.getFullYear() && ct.getMonth() == at.getMonth() && ct.getDate() == at.getDate()){// gleicher tag
      prefix = "heute um ";
    } else if (tm.getFullYear()==at.getFullYear() && tm.getMonth() == at.getMonth() && tm.getDate() == at.getDate()){// morgen
      prefix = "morgen um ";
    } else { // > morgen
      prefix = "am "+at.getDate()+"."+(at.getMonth()+1)+". um ";
    }
    return prefix + expandNumberString(at.getHours(),2)+":"+expandNumberString(at.getMinutes(),2)+":"+expandNumberString(at.getSeconds(),2)+":";
  }
  function unparseTime(string) {
    // heute um 22:43:54:442, etc zu timestamp
    var ct = currentTime();
    var s = string.replace(/\t/g, "").split(" ");
    //setting Date
    if (string.includes("heute")){
      var time = new Date(ct.getFullYear(), ct.getMonth(), ct.getDate())
    }else if (string.includes("morgen")) {
      var time = new Date(ct.getFullYear(), ct.getMonth(), ct.getDate() + 1)
    }else{
      var time = new Date(ct.getFullYear(), s[1].split(".")[1] - 1, s[1].split(".")[0])
    }
    //setting Time
    time.setHours(s[s.length - 1].split(":")[0]);
    time.setMinutes(s[s.length - 1].split(":")[1]);
    time.setSeconds(s[s.length - 1].split(":")[2]);
    return Date.parse(time)+parseInt(s[s.length - 1].split(":")[3]); //dont know how to add milliseconds to Date object...
  }
  function getTimeDiffAsString(timestamp){
    var ct = Date.parse(currentTime());
    var difference = parseInt((timestamp - ct) / 1000);
    var seconds    = difference % 60;
    difference     = (difference - difference % 60) / 60; //now in minutes
    var minutes    = difference % 60;
    var hours      = (difference - difference % 60) / 60;
    return hours+":"+expandNumberString(minutes,2)+":"+expandNumberString(seconds,2);
  }
  function currentTime(){
    var date 	= $("#serverDate").text().split("/");
	  var time 	= $("#serverTime").text().split(":");
	  var d		= new Date(
			parseInt(date[2]),
			parseInt(date[1]-1),
			parseInt(date[0]),
			parseInt(time[0]),
			parseInt(time[1]),
			parseInt(time[2]),
			0);
	   return d;
   }
   function expandNumberString(number, expand_to){
     output = number+"";
     number = parseInt(number);
     for (var i = 1 ; i < expand_to; i++){
       var smallest = parseInt("1"+"0".repeat(i));
       if (number < smallest){
         output = "0"+output;
       }
     }
     return output;
   }
   function appendUnitSymbols(units, td_handler){
     if ("spy" in units) {
       td_handler.append(
         $("<span>").append($("<img>").attr("src", "https://dsde.innogamescdn.com/asset/b8e610d/graphic/command/spy.png"))
       )
     }
     if ("knight" in units) {
       td_handler.append(
         $("<span>").append($("<img>").attr("src", "https://dsde.innogamescdn.com/asset/b8e610d/graphic/command/knight.png"))
       )
     }
     if ("snob" in units) {
       td_handler.append(
         $("<span>").append($("<img>").attr("src", "https://dsde.innogamescdn.com/asset/b8e610d/graphic/command/snob.png"))
       )
     }
   }
});
