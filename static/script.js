document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector("form");

    form.addEventListener("submit", function () {

        const button = document.querySelector("button");

        button.innerText = "Analyzing Resume...";
        button.disabled = true;

    });

});
