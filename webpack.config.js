const path = require('path');
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = {
    plugins: [new CompressionPlugin()],
    resolve: {
        extensions: ["", ".webpack.js", ".web.js", ".js", ".ts"]
    },
    entry: {
        map: './frontend/ts/map.ts',
        modals: './frontend/ts/modals.ts',
        form_functions: './frontend/ts/form_functions.ts',
        calendar: './frontend/ts/calendar.ts',
        leaflet_settings: './frontend/ts/leaflet_settings.ts',
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                loader: 'awesome-typescript-loader',
                exclude: /static/,
                options: {ignoreDiagnostics: [2686]},
            },
            {
                test: /\.css$/i,
                use: ['style-loader', 'css-loader'],
            },
            {
                test: /\.(png|jpe?g|gif|svg)$/i,
                loader: 'file-loader',
            },
            {
                test: /\.less$/i,
                use: ['style-loader', 'css-loader', 'less-loader'],
            }
        ],
    },
    resolve: {
        extensions: ['.ts', '.tsx', '.js'],
    },
    output: {
        path: path.resolve(__dirname, 'apps/dpnk/static/js/dist')
    },
    mode: "development",
}
