document.addEventListener("DOMContentLoaded", function () {

    const languageFilter = document.getElementById("language");

    if (!languageFilter) return;

    const updateURL = () => {

        const newURL = new URL(window.location.href);
        const languageValue = languageFilter.value;

        if (languageValue) {
            newURL.searchParams.set("language", languageValue);
        } else {
            newURL.searchParams.delete("language");
        }

        window.location.href = newURL.toString();
    };

    languageFilter.addEventListener("change", updateURL);
});