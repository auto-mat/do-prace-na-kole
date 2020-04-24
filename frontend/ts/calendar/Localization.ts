import "../leaflet";
import {drawLocales, Language} from 'leaflet-draw-locales';
import LocalizedStrings from 'localized-strings';

const strings = new LocalizedStrings(
    {
        en:{
            save: "Save",
            save_track: "Save track",
            trip_to: "To work",
            trip_from: "Home",
            recreational: "Recreational trip",
            manual_entry: "Enter distance by hand",
            draw_track: "Draw route into map",
            upload_gpx: "Upload GPX file",
            connection_error: "Connection error",
            today: "Today",
            month_calendar: "Calendar",
            week_calendar: "List",
            vacation: "Vacation",
            event: "Event",
            enter_distance_fist: "You need to enter the distance you traveled",
            min_distance_error: "You cannot enter trips less than ",
            min_duration_error: "You cannot enter trips less than ",
        },
        cs:{
            save: "Uložit",
            save_track: "Uložit trasu",
            trip_to: "Do práce",
            trip_from: "Domu",
            recreational: "Výlet",
            manual_entry: "Zadat vzdálenost ručně",
            draw_track: "Nakreslit trasu do mapy",
            upload_gpx: "Nahrát GPX soubor",
            connection_error: "Chyba připojení",
            today: "Dnes",
            month_calendar: "Kalendář",
            week_calendar: "Seznam",
            vacation: 'Dovolená',
            event: 'Akce',
            enter_distance_fist: 'Nejdříve zadejte vzdalenost.',
            max_distance_error: 'Vzdalenost nesmí být delší než 999 km. Pokud jste opravdu tak daleko jeli, kontaktujte helpdesk.',
            min_distance_error: 'Cesta se počítá od minimální vzdálenost ',
            min_duration_error: 'Minimální doba je ',
        }
    },
    {
        customLanguageInterface: function(){return document.documentElement.lang},
    },
);

export function load_strings(): typeof strings {
    // any TODO
  //  let locale = drawLocales(<Language>document.documentElement.lang);
//    locale.draw.toolbar.finish.text=strings.save;
 //   locale.draw.toolbar.finish.title=strings.save_track;
    return strings;
}
