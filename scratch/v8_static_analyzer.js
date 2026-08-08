const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO = 'D:\\GithubDesktopClone\\Anki_AI_Learning_Hub';

const jsFiles = [
    'web/js/bridge.js',
    'web/js/utils.js',
    'web/js/hint_system.js',
    'web/js/app.js'
];

console.log('=== V8 JAVASCRIPT AST & SYNTAX AUDIT ===');

jsFiles.forEach(relPath => {
    const fullPath = path.join(REPO, relPath);
    if (!fs.existsSync(fullPath)) return;
    const code = fs.readFileSync(fullPath, 'utf8');
    try {
        new vm.Script(code, { filename: relPath });
        console.log(`[PASS] ${relPath}: Syntax is 100% valid V8 JavaScript!`);
    } catch (err) {
        console.error(`[FAIL] ${relPath}: Syntax error!`, err.message);
    }
});
