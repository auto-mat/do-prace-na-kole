export function show_message(msg: string) {
    $("#message-modal-body").text(msg);
    $('#message-modal').modal({show:true});
}
