
/*

The UI components are controlled in part client side.

- Each node that needs control is given ID's such as 'choice-<base64-id-xpath>'
- Nodes can be blurred - with the 'yangui-disable' class
- Nodes can be collapsed - without the `show` class or shown with the `show` class
- Some nodes have actions (disable/enable a case) which are entirely client side.

There are performance impacts with big data models - however this could easily
be refactored to avoid loading the entire contents of presence containers if there
is no data underneath.

However for data models with data spread across a large model this may not be
enough - splitting the model into a number of tabs - and forcing a 'save' (i.e.
download a new LIBYANG_USER_PAYLOAD before changing tabs. This will allow the
DOM to flush the div's of the tabs which are no longer in focus. There is an
advantage of this that the user cannot create too much data in one place.
The other advantage is less interesting containers can be less clear on the UI.

*/


function yangui_default_mousetrap(){
  Mousetrap.reset();
  Mousetrap.bind(['command+z', 'ctrl+z'], function() { yangui_undo(); });
  Mousetrap.bind(['command+o', 'ctrl+o'], function() { yangui_upload(); });
  Mousetrap.bind(['command+s', 'ctrl+s'], function() { save_payload(); });
  Mousetrap.bind('y s', function() { submit_payload(); });
  Mousetrap.bind('y n', function() { new_payload(); });
  Mousetrap.bind('y v', function() { validate_payload(); });
  Mousetrap.bind('y d', function() { debug_payload(); });
  Mousetrap.bind('esc esc', function() { cancelMessages(); });
}

function new_payload(){
  window.location.replace("/web/"+LIBYANG_MODEL);
}

function enable_validate_save_buttons(){
  $(document.getElementById("yangui-validate")).removeClass("yangui-disable");
  $(document.getElementById("yangui-save")).removeClass("yangui-disable");
}

function yangui_undo(){
  /*
  The UI holds a copy of the data tree as LIBYANG_USER_PAYLOAD.

  Each action the user takes on the UI causes a change to be added to the LIBYANG_CHANGES list.
  The actions contain not just the action, path, values needed by yangvoodoo's Merger - but
  also enough information to be able to undo the changes on the UI.

  Since the server always process the LIBYANG_USER_PAYLOAD + LIBYANG_CAHNGES every time (i.e.
  there is no server state) then simply cleaning up the UI and popping the change from the list
  is sufficient to implement the undo.
  */
  undo = LIBYANG_CHANGES.pop();
  if(!undo){
    return;
  }

  if(undo.undelete_css){
    $(document.getElementById(undo.undelete_css)).removeClass('yangui-deleted');
  }

  if(undo.disable_css){
    $(document.getElementById(undo.disable_css)).addClass('yangui-disable');
  }

  if(undo.update_field){
    if(!undo.update_value){
      undo.update_value='';
    }
    document.getElementById(undo.update_field).value = undo.update_value;
  }

  if(undo.update_select){
    $(document.getElementById(undo.update_select)).selectpicker('val', undo.update_value);
  }

  if(undo.update_checkbox){
    if(undo.update_checkbox == "on"){
      val=true;
    }else{
      val=false;
    }
    $(document.getElementById(undo.update_checkbox)).prop('checked', val);
  }

  if(LIBYANG_CHANGES.length==0){
    $(document.getElementById("yangui-undo")).addClass("yangui-disable");
  }

  yangui_debug(null, "Undo change... "+atob(undo.base64_path) + "  " +undo.value);
}


function start_yangui_spinner(text){
  $(document.getElementById("yangui-spinner")).removeClass("yangui-hidden");
  document.getElementById("yangui-spinnertext").innerHTML=text;
}

  function stop_yangui_spinner(){
  $(document.getElementById("yangui-spinner")).addClass("yangui-hidden");
  document.getElementById("yangui-spinnertext").innerHTML="";
}

function cancelMessage(theme){
  if(parseInt($(document.getElementById('yangui-msg-'+theme)).data('yangui-hide-at')) < Date.now()){
    $(document.getElementById('yangui-msg-'+theme)).hide();
    $(document.getElementById('yangui-msg-'+theme)).html("");
  }
}

function cancelMessages(){
  /* Bootstrap alerts are not used because they are too small */
  $(document.getElementById('yangui-msg-danger')).html("");
  $(document.getElementById('yangui-msg-success')).hide("");
  $(document.getElementById('yangui-msg-danger')).hide();
  $(document.getElementById('yangui-msg-success')).hide();
}

function showMessage(title, message, theme, timeout) {
  $(document.getElementById('yangui-msg-'+theme)).data('yangui-hide-at', Date.now());
  $(document.getElementById('yangui-msg-'+theme)).html('<strong>'+title+'</strong><br/>' + message);
  $(document.getElementById('yangui-msg-'+theme)).data('yangui-hide-at', Date.now()+timeout);
  $(document.getElementById('yangui-msg-'+theme)).show();
  if(timeout){
    setTimeout(function() {
      cancelMessage(theme);
    }, timeout+1000);
  }
}

function yangui_debug(path, message){
  if(path){
    $(document.getElementById('yangui-msg-normal')).html("Path:" + atob(path)+ " " + message + " ("+LIBYANG_CHANGES.length+")");
  }else{
    $(document.getElementById('yangui-msg-normal')).html(message);
  }
}


function leaf_change(d, h){
  enable_validate_save_buttons();
}

function get_start_value(i){
  return "a";
}

function leaf_blur(b_path, h){
  new_val=$(h).val();
  old_val=$(h).data('yangui-start-val');
  if(old_val!=new_val){
    if(!new_val){
      if(old_val){ // make sure the text box isn't empty
        LIBYANG_CHANGES.push({"action": "delete", "base64_path": b_path, "value":"", "update_field": b_path, "update_value": old_val});
        yangui_debug(b_path, "delete from "+ old_val );
        $(h).data('yangui-start-val', undefined)
      }
    }else{
     LIBYANG_CHANGES.push({"action": "set", "base64_path": b_path, "value":h.value, "update_field": b_path, "update_value": old_val});
     yangui_debug(b_path, "changed from "+ old_val +" to "+new_val);
     $(h).data('yangui-start-val', new_val)
    }
    $(document.getElementById("yangui-undo")).removeClass("yangui-disable");
  }
}

function leaf_focus(b_path, h){
}

function select_change(b_path, h){
  enable_validate_save_buttons();
  old_val=$(h).data('yangui-start-val');
  new_val=h.value;
  LIBYANG_CHANGES.push({"action": "set", "base64_path": b_path, "value":h.value, "update_select": b_path, "update_value": old_val});
  yangui_debug(b_path, "changed "+ old_val +" to "+new_val);
  $(h).data('yangui-start-val', new_val)
  $(document.getElementById("yangui-undo")).removeClass("yangui-disable");
}

function check_change(b_path, h){
  enable_validate_save_buttons();
  old_val=$(h).data('yangui-start-val');
  if($(document.getElementById(b_path)).is(":checked")){
    new_val='on';
  }else{
    new_val='off';
  }
  LIBYANG_CHANGES.push({"action": "set_boolean", "base64_path": b_path, "value":new_val, "update_checkbox": b_path, "update_value": old_val});
  yangui_debug(b_path, "changed "+ old_val +" to "+new_val);
  $(h).data('yangui-start-val', new_val)
  $(document.getElementById("yangui-undo")).removeClass("yangui-disable");
}


function empty_change(b_path, h){
  enable_validate_save_buttons();
  old_val=$(h).data('yangui-start-val');
  if($(document.getElementById(b_path)).is(":checked")){
    new_val='on';
  }else{
    new_val='off';
  }
  LIBYANG_CHANGES.push({"action": "set_empty", "base64_path": b_path, "value":new_val, "update_checkbox": b_path, "update_value": old_val});
  yangui_debug(b_path, "changed "+ old_val +" to "+new_val);
  $(h).data('yangui-start-val', new_val)
  $(document.getElementById("yangui-undo")).removeClass("yangui-disable");
}

function empty_blur(d, h){
  console.log("Empty leaf has blurred\n\nData XPATH:" + d + "\nHTMLNode: "+h);
  enable_validate_save_buttons();
}

function add_list_element(d, s, u){
  Mousetrap.bind('escape', function() { close_new_item(); });
  $(document.getElementById("yangui-create-list-button")).data("yangui-for-datapath", d);
  $(document.getElementById("yangui-create-list-button")).data("yangui-for-schemapath", s);
  $(document.getElementById("yangui-create-list-button")).data("yangui-for-type", "list");
  $(document.getElementById("yangui-create-list-button")).data("yangui-containing-div", u );
  start_yangui_spinner('');
  payload={ "type":"list", "data_xpath": d, "schema_xpath":s, "yang_model":LIBYANG_MODEL}

  $.ajax({
      type: "POST",
      url: AJAX_BASE_SERVER_URL+"/get-list-create-page",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
          stop_yangui_spinner();
          $("#yanguiNewItemModal").modal('show');
          $("#yanguiNewItemContents").html(response);
      },
      error: function(xhr, options, err) {
        showMessage("Connectivity Error", handle_ajax_error(xhr), 'danger');
        stop_yangui_spinner();
      }
  });
}

function close_new_item(){
  yangui_default_mousetrap();
  $("#capture-new-item").addClass("yangui-hidden");
  $("#capture-new-item-list-contents").innerHTML="Not Implemented - fetch contents from a server specific to list";
}

function create_new_item(){
  // Create anew item in a list.
  yangui_default_mousetrap();
  list_type=$(document.getElementById("yangui-create-list-button")).data('yangui-for-type');
  div_to_append = $(document.getElementById("yangui-create-list-button")).data('yangui-containing-div');
  payload = {
    "base64_data_path": $(document.getElementById("yangui-create-list-button")).data('yangui-for-datapath'),
    "base64_schema_path": $(document.getElementById("yangui-create-list-button")).data('yangui-for-schemapath'),
    key_values:[],
    "yang_model":LIBYANG_MODEL
  }

  $("#yanguiNewItemContents").find("input,select").each(function(index){
    // Note: drop-down boxes using the bootstrap-select don't behave thee same as regular drop-down boxes
    // searching for select and input returns internal components of the bootstrap-select so we have to filter
    // for only elements that contain yangui-field-type
    if($(this).data("yangui-field-type")){
      if(list_type == "leaf-list"){
        payload.key_values.push([".", this.value]);
      }
      if(list_type == "list"){
        payload.key_values.push([$(this).data("yangui-keyname"), this.value]);
      }
    }
  });

  $.ajax({
      type: "POST",
      url: AJAX_BASE_SERVER_URL+"/create-"+list_type,
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
          stop_yangui_spinner();

          $(document.getElementById("collapse-"+div_to_append)).append(response);
          LIBYANG_CHANGES.push({"action": "create_list_xpath", "base64_path": payload.base64_data_path, "value":payload.key_values ,"undo_to_do":"todo - need more info like list elemetn html id"});
          $("#yanguiNewItemModal").modal('hide');
          enable_validate_save_buttons();


      },
      error: function(xhr, options, err) {
        showMessage("Connectivity Error", handle_ajax_error(xhr), 'danger');
        stop_yangui_spinner();
      }
  });

}

function remove_list_element(b_path){
  LIBYANG_CHANGES.push({"action": "delete_list_xpath", "base64_path": b_path, "undelete_css": "list-item-"+b_path, "value":null});
  $(document.getElementById("list-item-"+b_path)).addClass('yangui-deleted');
  $(document.getElementById("yangui-undo")).removeClass("yangui-disable");
  enable_validate_save_buttons();
}

function enable_case(b_path, b_parent_path){
  /* Give the base64 path of the choice container (i.e. our case's parent)
     loop around all span's
     - hide any enable case buttons
     - show our remove-case path
     - remove the opactity disabling of our case
     - expand the our case (add show)
  */
  choiceDiv = $(document.getElementById(b_parent_path));
  choiceDiv.find("span").each(function(index){
      if(this.id == "remove-case-" + b_path){
        $(this).removeClass("yangui-hidden");
      }
      if(this.id.startsWith("enable-case-")){
        $(this).addClass("yangui-hidden");
      }
  });
  caseDiv=$(document.getElementById("case-" + b_path ));
  caseDiv.removeClass('yangui-disable');
  caseDiv.addClass('show');
  caseDiv.find("input").each(function(index){
    $(this).removeAttr('disabled');
  });
}

function disable_case(b_parent_path){
  // Given the base64 path of the choice container (i.e. our case's parent)
  // - loop around all span's
  // use the button name remove-case-<base64path> to disable the div case-<base64path>
  // hide all the remove-case-<base64path> buttons
  // show all the enable-case-<base64path> buttons
  choiceDiv = $(document.getElementById(b_parent_path));
  choiceDiv.find("span").each(function(index){
      $(document.getElementById(this.id.substring(7)) ).addClass('yangui-disable');
      if(this.id.startsWith("remove-case-")){
        $(this).addClass("yangui-hidden");
      }
      if(this.id.startsWith("enable-case-")){
        $(this).removeClass("yangui-hidden");
      }
  });
}

function add_leaflist_item(d, s, u){
  Mousetrap.bind('escape', function() { close_new_item(); });
  // $("#capture-new-item").removeClass("#yangui-hidden");
  start_yangui_spinner('');
  payload={ "type":"list", "data_xpath": d, "schema_xpath":s, "yang_model":LIBYANG_MODEL}
  $(document.getElementById("yangui-create-list-button")).data("yangui-for-type", "leaf-list");
  $(document.getElementById("yangui-create-list-button")).data("yangui-for-datapath", d);
  $(document.getElementById("yangui-create-list-button")).data("yangui-for-schemapath", s);
  $(document.getElementById("yangui-create-list-button")).data("yangui-containing-div", u );
  $.ajax({
      type: "POST",
      url: AJAX_BASE_SERVER_URL+"/get-leaf-list-create-page",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
          stop_yangui_spinner();
          $("#yanguiNewItemModal").modal('show');
          $("#yanguiNewItemContents").html(response);
          $(document.getElementById(d)).selectpicker('show');
      },
      error: function(xhr, options, err) {
        showMessage("Connectivity Error", handle_ajax_error(xhr), 'danger',5000);
        stop_yangui_spinner();
      }
  });
}

function remove_leaflist_item(b_path){
  // Deleting items is handled in the UI building a list of XPATH's to remove
  // potentially we could give an undo button on the UI by simply removing the CSS
  // and making sure the item is removed from the changes list.
  LIBYANG_CHANGES.push({"action": "delete_list_xpath", "base64_path": b_path, "undelete_css": "leaflist-item-"+b_path, "value":null});
  $(document.getElementById("leaflist-item-"+b_path)).addClass('yangui-deleted');
  $(document.getElementById("yangui-undo")).removeClass("yangui-disable");
  enable_validate_save_buttons();
}

function handle_ajax_error(xhr){
  if(xhr.status==0){
    return "Connection to server failed - (0)"
  }
  return xhr.responseText + " ("+xhr.status+")"
}

function list_element_expand(b_path,uuid){
  console.log(b_path);
  if($(document.getElementById("collapse-"+uuid)).data('yangui-collapse')=='collapse'){
    ELEMENTS_EXPANDED_BY_USER[uuid] = true;
  }else{
    ELEMENTS_EXPANDED_BY_USER[uuid] = false;
  }
}

function presence_container_expand(b_path, uuid){
  containerDiv = $(document.getElementById(b_path));
  if(containerDiv.hasClass("yangui-disable")){
    containerDiv.removeClass("yangui-disable");
    LIBYANG_CHANGES.push({"action": "set", "base64_path": b_path, "value":"", "disable_css": b_path});
    $(document.getElementById("yangui-undo")).removeClass("yangui-disable");
    enable_validate_save_buttons();
  }

  if($(document.getElementById("collapse-"+uuid)).data('yangui-collapse')=='collapse'){
    ELEMENTS_EXPANDED_BY_USER[uuid] = true;
  }else{
    ELEMENTS_EXPANDED_BY_USER[uuid] = false;
  }
}

function modal_visibility(modal, visibility){
  $("#"+modal).modal(visibility);
}
function upload_payload (){
  modal_visibility("yanguiUploadModal", "show");
}

function validate_payload(){
  cancelMessages();
  for(index in LIBYANG_CHANGES){
    console.log("Change: "+ JSON.stringify(LIBYANG_CHANGES[index]));
  }
  if($(document.getElementById("yangui-validate")).hasClass("yangui-disable")){
    return;
  }
  start_yangui_spinner("Validating.....");

  payload = {"payload": LIBYANG_USER_PAYLOAD, "changes": LIBYANG_CHANGES}
  $.ajax({
      type: "POST",
      url: AJAX_BASE_SERVER_URL+"/validate",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
        // $(document.getElementById("capture-new-item-list-contents")).innerHTML=response;
        stop_yangui_spinner();
        showMessage('<i class="fa fa-2x fa-smile-o" aria-hidden="true"></i>',"payload successfully validated","success", 2500);
      },
      error: function(xhr, options, err) {
        showMessage("Validation Error", handle_ajax_error(xhr), 'danger');
        stop_yangui_spinner();
      }
  });
}

function debug_close(){
  $(document.getElementById("yangui-content-debug")).val("");
  modal_visibility('yanguiDebugModal', 'hide');
}

function debug_payload(){
  start_yangui_spinner("Merging....");
  $(document.getElementById("yangui-content-debug")).val("");
  payload = {"payload": LIBYANG_USER_PAYLOAD, "changes": LIBYANG_CHANGES}
  $.ajax({
      type: "POST",
      url: AJAX_BASE_SERVER_URL+"/download",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
        $(document.getElementById("yangui-content-debug")).val(JSON.stringify( JSON.parse(response).new_payload,null,4));


        $("#yanguiDebugModal").modal('show');
        stop_yangui_spinner();
      },
      error: function(xhr, options, err) {
        showMessage("Debug Error", handle_ajax_error(xhr), 'danger',  5000);
        stop_yangui_spinner();
        $("#yanguiDebugModal").modal('hide');
      }
  });

}

function download_payload(){
  cancelMessages();
  if($(document.getElementById("yangui-save")).hasClass("yangui-disable")){
    return;
  }
  start_yangui_spinner("Downloading.....");

  payload = {"payload": LIBYANG_USER_PAYLOAD, "changes": LIBYANG_CHANGES}
  $.ajax({
      type: "POST",
      url: AJAX_BASE_SERVER_URL+"/download",
      crossDomain: true,
      data: JSON.stringify(payload),
      cache: false,
      success: function(response) {
        stop_yangui_spinner();
        download(JSON.parse(response).new_payload , 'keep-me-safe.json', 'application/json');
      },
      error: function(xhr, options, err) {
        showMessage("Validation Error", handle_ajax_error(xhr), 'danger',  5000);
        stop_yangui_spinner();
      }
  });
}

function download(content, fileName, contentType) {
    var a = document.createElement("a");
    var file = new Blob([JSON.stringify(content)], {type: contentType});
    a.href = URL.createObjectURL(file);
    a.download = fileName;
    a.click();
}

window.addEventListener('beforeunload', function (e) {
  if(LIBYANG_CHANGES.length > 0){
    e.preventDefault();
    e.returnValue = '';
  }
});

function yangui_welcome(){
  yangui_debug(null, '<strong>'+YANGUI_TITLE+'</strong> - loaded '+LIBYANG_MODEL);
}
