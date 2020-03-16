// ==UserScript==
// @name        DS_Timer_SHOW
// @namespace   de.die-staemme
// @version     0.1
// @description Export your Attack-Details for DS_Timer
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       unsafeWindow
// @match       https://*.die-staemme.de/game.php?*screen=info_village*
// @copyright   2016+, Raznarek, stabel
// ==/UserScript==

var $ = typeof unsafeWindow != 'undefined' ? unsafeWindow.$ : window.$;

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
      var target_id = getPageAttribute("id");
      console.log('127.0.0.1:5000/show/'+getDomain()+'/target_id/'+target_id)

      $.ajax({ url: 'http://127.0.0.1:5000/show/'+getDomain()+'/target_id/'+target_id,
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
        if (response.length == 0){ // Abbruch, wenn keine Angriffe geplant
          console.log("keine geplanten Angriffe")
          return
        }
        // create table for outgoings
        if($("#commands_outgoings").length==0){
          var note_table = $("#message").closest("table");
          //$("<p>Test<p>").insertAfter(note_table);
          var commands_outgoings = $("<div>")
            .attr("id", "commands_outgoings")
            .insertAfter(note_table);
          var command_table = $("<table>").appendTo(commands_outgoings)
            .attr("id", "command_table")
            .attr("class", "vis").attr("style", "width:100%");
          var command_header = $("<tr>").appendTo(command_table)
            .append($("<th>").attr("width", "52%").html("Eigene Befehle"))
            .append($("<th>").attr("width", "33%").html("Ankunft"))
            .append($("<th>").attr("width", "15%").html("Ankunft in"));
        } else {
          var command_table = $("#commands_outgoings").find("table").first();
        }
        for (action of response){
          var arrival_time = new Date(action["arrival_time"]);
          var mseconds = expandNumberString(action["milliseconds"],3)
          var arrival_time= parseTime(arrival_time);
          $("<tr>").attr("class", "command-row").appendTo(command_table)
            .append($("<td>").append($("<a>").attr("href", "/game.php?village="+action["source_id"]+"&screen=overview").html(action["source_id"])))
            .append($("<td>").html(arrival_time).append($("<span>").html(mseconds).attr("class", "grey small")))
            .append($("<td>").append($("<span>").html("TODO").attr("class","grey small")))
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
});
