(() => {
    "use strict";

    const dataElement = document.getElementById("yokai-game-data");
    if (!dataElement) return;

    const yokais = JSON.parse(dataElement.textContent);
    const image = document.getElementById("guess-image");
    const form = document.getElementById("guess-form");
    const guessInput = document.getElementById("guess-input");
    const feedback = document.getElementById("guess-feedback");
    const scoreDisplay = document.getElementById("guess-score");
    const answer = document.getElementById("guess-answer");
    const answerName = document.getElementById("answer-name");
    const answerTypes = document.getElementById("answer-types");
    const revealButton = document.getElementById("reveal-answer");
    const nextButton = document.getElementById("next-guess");

    let currentYokai = null;
    let previousSlug = null;
    let score = 0;
    let revealed = false;

    const normalizeName = (value) => value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase("es")
        .trim();

    const chooseYokai = () => {
        const options = yokais.filter((yokai) => yokais.length < 2 || yokai.slug !== previousSlug);
        return options[Math.floor(Math.random() * options.length)];
    };

    const startRound = () => {
        if (!yokais.length) {
            feedback.textContent = "No hay Yokai disponibles para jugar.";
            form.hidden = true;
            revealButton.hidden = true;
            image.hidden = true;
            return;
        }

        currentYokai = chooseYokai();
        previousSlug = currentYokai.slug;
        revealed = false;
        image.src = currentYokai.image_url;
        image.alt = "Silueta misteriosa";
        image.classList.add("guess-silhouette");
        answer.hidden = true;
        answerName.textContent = "";
        answerTypes.replaceChildren();
        guessInput.value = "";
        guessInput.disabled = false;
        form.querySelector("button[type='submit']").disabled = false;
        revealButton.hidden = false;
        nextButton.hidden = true;
        feedback.textContent = "Escribe tu respuesta o pulsa «Revelar».";
        guessInput.focus();
    };

    const revealCurrent = () => {
        if (revealed || !currentYokai) return;
        revealed = true;
        image.classList.remove("guess-silhouette");
        image.alt = currentYokai.name;
        answerName.textContent = currentYokai.name;
        currentYokai.types.forEach((type) => {
            const badge = document.createElement("span");
            badge.className = `badge type-${type.css_class}`;
            badge.textContent = type.name;
            answerTypes.append(badge);
        });
        answer.hidden = false;
        guessInput.disabled = true;
        form.querySelector("button[type='submit']").disabled = true;
        revealButton.hidden = true;
        nextButton.hidden = false;
    };

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        if (revealed || !currentYokai) return;
        if (!guessInput.value.trim()) {
            feedback.textContent = "Escribe un nombre para intentar adivinar.";
            guessInput.focus();
            return;
        }
        if (normalizeName(guessInput.value) === normalizeName(currentYokai.name)) {
            score += 1;
            scoreDisplay.textContent = String(score);
            feedback.textContent = "¡Correcto!";
            revealCurrent();
        } else {
            feedback.textContent = "No es ese Yokai. ¡Prueba otra vez o pulsa «Revelar»!";
            guessInput.select();
        }
    });

    revealButton.addEventListener("click", () => {
        if (!currentYokai) return;
        feedback.textContent = `Era ${currentYokai.name}.`;
        revealCurrent();
    });

    nextButton.addEventListener("click", startRound);
    startRound();
})();
