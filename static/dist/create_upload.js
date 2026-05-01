const fileInput = document.getElementById("id_file");
const titleInput = document.getElementById("id_title");

fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) {
        titleInput.value = file.name;
    }
});