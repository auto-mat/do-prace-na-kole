//@ts-ignore
let helpdesk_iframe_url: string = window.helpdesk_iframe_url;

$(document).ready(function() {
    $(".normalmodal").modal({
        show: false,
    });

    $('.notifications-shower').click(function () {
        update_notifications_modal_contents();
        $('#notificationswindow').modal("show");
    });
    $('#notificationswindow-close').click(function () {
        $("#notificationswindow").modal("hide");
    });

    $('.helpdesk-shower').click(function () {
        $('#helpdeskiframe').attr('src', helpdesk_iframe_url);
        $('#helpdeskwindow').modal("show");
    });

    $('.helpdesk-shower').click(function () {
        $('#helpdeskiframe').attr('src', helpdesk_iframe_url);
        $('#helpdeskwindow').modal("show");
    });

    $('.helpdesk-close').click(function() {
        $('#helpdeskiframe').attr('src', '');
        $("#helpdeskwindow").modal("hide");
    });
});

interface NotificationData {
    icon: string;
    url: string;
}

interface DjangoNotification {
    data: NotificationData;
    verb: string;
    timestamp: number;
    slug: string;
    unread: boolean;
}

interface DjangoNotifications {
    all_list?: DjangoNotification[];
    all_count?: number;
    unread_count?: number;
    unread_list?: DjangoNotification[];
}

export class Notifications {
    public static notifications_list: DjangoNotifications;
}

function update_notifications_modal_contents () {
    let data = Notifications.notifications_list;
    //@ts-ignore
    const notify_menu_class: string = window.notify_menu_class
    var menus = document.getElementsByClassName(notify_menu_class);
    if (menus) {
        var messages = data.all_list.map(function (item: DjangoNotification) {
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

var dpnk_fill_notification_list = function (data: DjangoNotifications) {
    Notifications.notifications_list = data;
    let cl = $(".live_badge_count")[0].classList;
    let status_cls;
    for(var i = 0; i < cl.length; i++){
        if(cl[i].indexOf("status_") != -1){
            status_cls = cl[i];
        };
    };
    cl.remove(status_cls);
    cl.add(`status_${data.unread_count}`);
}
//@ts-ignore
window.dpnk_fill_notification_list = dpnk_fill_notification_list;
