function pad(n, width, z) {
    z = z || '0';
    n = n + '';
    return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}

function format_date(date){
    return date.getFullYear() + '-' + pad((date.getMonth() + 1).toString(), 2) + '-' + pad(date.getDate().toString(), 2);
}

function add_days(date, days){
    new_date = new Date(date);
    new_date.setDate(new_date.getDate() + days);
    return new_date;
}
