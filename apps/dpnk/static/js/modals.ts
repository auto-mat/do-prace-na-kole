function closeHelpdesk() {
    $('#helpdeskwindow').hide();
    $('#helpdeskiframe').attr('src','');
}

function showHelpdesk() {
    $('#helpdeskiframe').attr('src', window.helpdesk_iframe_url);
    $('#helpdeskwindow').show();
};


function closeNotifications() {
    $('#notificationswindow').hide();
}

function showNotifications() {
    $('#notificationswindow').show();
};

function dpnk_fill_notification_list(data) {
    var menus = document.getElementsByClassName(notify_menu_class);
    if (menus) {
        var messages = data.all_list.map(function (item) {
            var message = "";
            if(item.data && item.data.icon) {
                message = `${message} <img class='notification-icon' src='${item.data.icon}'/>`;
            }
            if(typeof item.verb !== 'undefined'){
                message = `${message} ${item.verb}`;
            }
            if(typeof item.timestamp !== 'undefined'){
                message = `${message} <time class='timeago notification-timestamp' datetime='${item.timestamp}'>  </time>`;
            }
            return `<li class="notification-list-item notification-list-item-${item.unread && 'un' || ''}read"> <a href="/inbox/notifications/mark-as-read/${item.slug}/?next=${((item.data && item.data.url) || "#" )}">${message}</a></li>`;
        }).join('')

        for (var i = 0; i < menus.length; i++){
            menus[i].innerHTML = messages;
            if(data.all_list.length == 0) {
                menus[i].innerHTML = "<b>0</b> <i class='fas fa-times'></i> <i class='fas fa-envelope'></i>";
            }
        }
        $("time.timeago").timeago();
    }
}
