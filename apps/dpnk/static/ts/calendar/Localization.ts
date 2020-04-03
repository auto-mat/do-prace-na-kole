import LocalizedStrings from 'localized-strings';

export function load_strings(): LocalizedStringsMethods {
    let strings = new LocalizedStrings(
        {
            en:{
                save: "Save",
                save_track: "Save track",
            },
            cs:{
                save: "Uložit",
                save_track: "Uložit trasu",
            }
        },
        {
            customLanguageInterface: function(){return document.documentElement.lang},
        },
    );

    L.drawLocal.draw.toolbar.finish.text=strings.save;
    L.drawLocal.draw.toolbar.finish.title=strings.save_track;
    return strings;
}
