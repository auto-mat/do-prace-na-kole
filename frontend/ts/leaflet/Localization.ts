import LocalizedStrings from 'localized-strings';
import 'leaflet';
import 'leaflet-draw';
import {drawLocales, Language} from 'leaflet-draw-locales';

const strings = new LocalizedStrings(
    {
        en:{
            save: "Save",
            save_track: "Save track",
            same_as: "Same as...",
        },
        cs:{
            save: "Uložit",
            save_track: "Uložit trasu",
            same_as: "Stejně jako...",
        }
    },
    {
        customLanguageInterface: function(){return document.documentElement.lang},
    },
);

export function load_strings(): typeof strings {
    let locale = drawLocales(<Language>document.documentElement.lang);
    locale.draw.toolbar.finish.text=strings.save;
    locale.draw.toolbar.finish.title=strings.save_track;
    return strings;
}
