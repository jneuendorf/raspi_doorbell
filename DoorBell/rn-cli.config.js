const path = require('path')


const directories = [
    __dirname,
    path.resolve(__dirname, '../')
]


module.exports = {
    getProjectRoots: () => directories,
    watchFolders: directories,
}
