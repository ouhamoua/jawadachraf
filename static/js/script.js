document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file');
    const preview = document.getElementById('preview');

    // Aperçu de l'image téléchargée
    if (fileInput && preview) {
        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) {
                preview.src = URL.createObjectURL(file);
                preview.style.display = 'block';
            } else {
                preview.src = '';
                preview.style.display = 'none';
            }
        });
    }

    // Message de chargement pendant la soumission
    if (uploadForm) {
        uploadForm.addEventListener('submit', () => {
            if (fileInput.files.length > 0) {
                console.log('Image en cours de traitement...');
            }
        });
    }
});