
/*

The UI components are controlled in part client side.

- Each node that needs control is given ID's such as 'choice-<base64-id-xpath>'
- Nodes can be blurred - with the 'yangui-disable' class
- Nodes can be collapsed - without the `show` class or shown with the `show` class
- Some nodes have actions (disable/enable a case) which are entirely client side.


*/


function yangui_default_mousetrap(){
  Mousetrap.reset();
  Mousetrap.bind(['command+z', 'ctrl+z'], function() { yangui_undo(); });
  Mousetrap.bind(['command+o', 'ctrl+o'], function() { yangui_upload(); });
  Mousetrap.bind(['command+s', 'ctrl+s'], function() { save_payload(); });
  Mousetrap.bind('y s', function() { submit_payload(); });
  Mousetrap.bind('y n', function() { new_payload(); });
  Mousetrap.bind('y v', function() { validate_payload(); });
}

function new_payload(){
  window.location.replace("/web/"+LIBYANG_MODEL);
}

function enable_validate_save_buttons(){
  $(document.getElementById("yangui-validate-button")).removeClass("yangui-disable");
  $(document.getElementById("yangui-save-button")).removeClass("yangui-disable");
}

function submit_payload(){
  alert("Do something here to merge the payload+changes and then do something interesting.....");
}

function yangui_undo(){
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
    $(document.getElementById("yangui-undo-button")).addClass("yangui-disable");
  }

  yangui_debug(null, "Undone change... "+JSON.stringify(undo));
}


function start_yangui_spinner(text){
  $(document.getElementById("yangui-spinner")).removeClass("yangui-hidden");
  document.getElementById("yangui-spinnertext").innerHTML=text;
}

  function stop_yangui_spinner(){
  $(document.getElementById("yangui-spinner")).addClass("yangui-hidden");
  document.getElementById("yangui-spinnertext").innerHTML="";
}

function addAlert(title, message, theme, id, timeout) {
    $('#alerts').append(
      '<div id="' + id + '" class="alert alert-' + theme + ' alert-dismissible fade show alertwider" role="alert">' +
      '<div class="alertwider">' +
      '<strong>'+title+'</strong><br/>' + message +
      '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
      '</div>' +
      '</div>');

    if(timeout){
      setTimeout(function() {
        this_alert = $(document.getElementById("success_validate_alert"));
        if(this_alert){
          this_alert.remove();
          }
        }, 1750);
    }
}

function adam_debug(){

}

function yangui_debug(path, message){
  if(path){
    document.getElementById("yangui-debug").innerHTML=atob(path)+ " " + message + " ("+LIBYANG_CHANGES.length+")";
  }else{
    document.getElementById("yangui-debug").innerHTML=message;
  }
}

function leaf_change(d, h){
  enable_validate_save_buttons();
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
    $(document.getElementById("yangui-undo-button")).removeClass("yangui-disable");
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
  $(document.getElementById("yangui-undo-button")).removeClass("yangui-disable");
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
  $(document.getElementById("yangui-undo-button")).removeClass("yangui-disable");
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
  $(document.getElementById("yangui-undo-button")).removeClass("yangui-disable");
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
        addAlert("Connectivity Error", handle_ajax_error(xhr), 'danger');
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
        addAlert("Connectivity Error", handle_ajax_error(xhr), 'danger');
        stop_yangui_spinner();
      }
  });

}

function remove_list_element(b_path){
  LIBYANG_CHANGES.push({"action": "delete_list_xpath", "base64_path": b_path, "undelete_css": "list-item-"+b_path, "value":null});
  $(document.getElementById("list-item-"+b_path)).addClass('yangui-deleted');
  $(document.getElementById("yangui-undo-button")).removeClass("yangui-disable");
  enable_validate_save_buttons();
}

function enable_case(b_path, b_parent_path){
  // Give the base64 path of the choice container (i.e. our case's parent)
  // loop around all span's
  // - hide any enable case buttons
  // - show our remove-case path
  // - remove the opactity disabling of our case
  // - expand the our case (add show)
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
        addAlert("Connectivity Error", handle_ajax_error(xhr), 'danger');
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
  $(document.getElementById("yangui-undo-button")).removeClass("yangui-disable");
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
    $(document.getElementById("yangui-undo-button")).removeClass("yangui-disable");
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
  $(document.getElementById("alerts")).empty();
  for(index in LIBYANG_CHANGES){
    console.log("Change: "+ JSON.stringify(LIBYANG_CHANGES[index]));
  }
  if($(document.getElementById("yangui-validate-button")).hasClass("yangui-disable")){
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
        addAlert('<i class="fa fa-2x fa-smile-o" aria-hidden="true"></i>',"payload succesfully validated","success","success_validate_alert",200);
      },
      error: function(xhr, options, err) {
        addAlert("Validation Error", handle_ajax_error(xhr), 'danger', "validation_error_alert");
        stop_yangui_spinner();
      }
  });
}

function download_payload(){
  $(document.getElementById("alerts")).empty();
  if($(document.getElementById("yangui-save-button")).hasClass("yangui-disable")){
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
        addAlert("Validation Error", handle_ajax_error(xhr), 'danger', "validation_error_alert");
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
