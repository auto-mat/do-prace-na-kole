const path = require('path');

module.exports = {
    entry: {
        map: './apps/dpnk/static/js/map.ts',
        modals: './apps/dpnk/static/js/modals.ts',
        form_functions: './apps/dpnk/static/js/form_functions.ts',
    },
    module: {
        rules: [
            {
                loader: 'ts-loader',
                options: {ignoreDiagnostics: [2304, 2339, 7006, 2393],},
                exclude: [/node_modules/, /static/],
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
