// read photos from file system
const fs = require('fs');
const path = require('path');

const photosDir = path.join(__dirname, 'telegram-images');

fs.readdir(photosDir, (err, files) => {
    if (err) {
        console.error('Error reading directory:', err);
        return;
    }

    const photoFiles = files.filter(file => /\.(jpg|jpeg|png|gif)$/.test(file));
    console.log('Photo files found:', photoFiles);
});

function renderPhoto(fileName) {
    const filePath = path.join(photosDir, fileName);
    if (fs.existsSync(filePath)) {
        
        return `<img src="${filePath}" alt="${fileName}">`;
    } else {
        console.error('File not found:', filePath);
        return 'Photo not found';
    }
}

function displayPhoto() {
    for (const file of photoFiles) {
        document.getElementById('photo-container').innerHTML = renderPhoto(file);
    }
}

displayPhoto()