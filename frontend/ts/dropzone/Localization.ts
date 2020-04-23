import LocalizedStrings from 'localized-strings';
import * as Dropzone from 'dropzone';
const dz = Dropzone
dz.autoDiscover = false;

const strings = new LocalizedStrings(
    {
        en:{
            dictDefaultMessage: 'Drag and drop gpx file to upload',
            dictFallbackMessage: 'Your browser does not support drag&drop file uploads.',
            dictFallbackText: 'Please use the fallback form below to upload your files like in the olden days.',
            dictFileTooBig: 'File is too big ({{filesize}}MiB). Max filesize: {{maxFilesize}}MiB.',
            dictInvalidFileType: 'Only valid GPX files are supported.',
            dictResponseError: 'Server responded with {{statusCode}} code.',

        },
        cs: {
            dictDefaultMessage: 'GPX soubory nahrajete přetažením, nebo kliknutím',
        }
    },
    {
        customLanguageInterface: function(){return document.documentElement.lang},
    },
);

export function load_strings_gpx(): typeof strings {
    Dropzone.prototype.defaultOptions.dictDefaultMessage = strings.dictDefaultMessage;
    Dropzone.prototype.defaultOptions.dictFallbackMessage = strings.dictFallbackMessage;
    Dropzone.prototype.defaultOptions.dictFallbackText = strings.dictFallbackText;
    Dropzone.prototype.defaultOptions.dictFileTooBig = strings.dictFileTooBig;
    Dropzone.prototype.defaultOptions.dictInvalidFileType = strings.dictInvalidFileType;
    Dropzone.prototype.defaultOptions.dictResponseError = strings.dictResponseError;
    return strings;
}
