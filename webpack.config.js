const path = require('path');

module.exports = {
    entry: {
        map: './apps/dpnk/static/ts/map.ts',
        modals: './apps/dpnk/static/ts/modals.ts',
        form_functions: './apps/dpnk/static/ts/form_functions.ts',
        calendar: './apps/dpnk/static/ts/calendar.ts',
    },
    module: {
        rules: [
            {
                loader: 'ts-loader',
                options: {ignoreDiagnostics: [2304, 2339, 7006, 2393],},
                exclude: [/node_modules/],
            },
        ],
    },
    resolve: {
        extensions: ['.ts', '.tsx', '.js'],
    },
    output: {
        path: path.resolve(__dirname, 'apps/dpnk/static/js/dist')
    }
}
