// =====================
// API Helpers
// =====================

const authToken = localStorage.getItem("authToken");
const headers = {
  Authorization: `Bearer ${authToken}`,
  "Content-Type": "application/json",
};

async function apiGet(path) {
  const res = await fetch(path, { headers });
  if (!res.ok) throw new Error(`GET ${path} failed`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed`);
  return res.json();
}

async function apiPut(path, body) {
  const res = await fetch(path, {
    method: "PUT",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PUT ${path} failed`);
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(path, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) throw new Error(`DELETE ${path} failed`);
  return res.json();
}

// =====================
// Page Logic
// =====================

async function getDueFlashcards(deckId){
    const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
    dueFlashcards.sort((a,b) => new Date(a.next_review_at) - new Date(b.next_review_at));

    return dueFlashcards;
}

async function showAndHideBack(){
    // add eventhanlder for the show answer button 
    const showAnswerButton = document.getElementById("show-answer");
    const backDiv = document.getElementById("back");
    showAnswerButton.addEventListener("click", async () => {
        await stopTimer();
        backDiv.classList.add("show");
    });
}


async function fillFrontAndBack(){
    const frontP = document.getElementById("front-p");
    const backP = document.getElementById("back-p");
    const noCardsLeft = await showReviewFinishedMessage();
    const backDiv = document.getElementById("back");
    if(noCardsLeft == true){
        // we have to nullify the front and back and also not show the show answer button
        document.getElementById("show-review").style.display = "none";
        return;
    }
    // use the global currentIndex to determine which flashcard we are looking at
    backDiv.classList.remove("show"); // hide the back again
    const currentFlashcard = reviewQueue[currentIndex];
    frontP.textContent = currentFlashcard.front;
    backP.textContent = currentFlashcard.back;
    await startTimer();
}

async function sendFeedback(){
    // we need to get the curernt flashcard"s id (referencing the global variable) 
    const badFeedbackButton = document.getElementById("bad");
    const midFeedbackButton = document.getElementById("mid");
    const goodFeedbackButton = document.getElementById("good");
    const currentFlashcard = reviewQueue[currentIndex];

    badFeedbackButton.addEventListener("click", async () => {
        currentIndex++;
        await fillFrontAndBack();
        await apiPost(`/flashcards/${currentFlashcard.id}/review`, {"feedback": "bad"});
    });
   midFeedbackButton.addEventListener("click", async () => {
        currentIndex++;
        await fillFrontAndBack();
        await apiPost(`/flashcards/${currentFlashcard.id}/review`, {"feedback": "mid"});
    });
    goodFeedbackButton.addEventListener("click", async () => {
        currentIndex++;
        await fillFrontAndBack();
        await apiPost(`/flashcards/${currentFlashcard.id}/review`, {"feedback": "good"});

    });

}   

async function cardActions() {
    const editButton = document.getElementById("edit-card");
    const deleteButton = document.getElementById("delete-card");
    const modal = document.getElementById("edit-modal");
    const closeButton = document.querySelector(".close-button");
    const editForm = document.getElementById("edit-form");
    const editFront = document.getElementById("edit-front");
    const editBack = document.getElementById("edit-back");

    editButton.addEventListener("click", () => {
        const currentFlashcard = reviewQueue[currentIndex];
        editFront.value = currentFlashcard.front;
        editBack.value = currentFlashcard.back;
        modal.style.display = "block";
    });

    deleteButton.addEventListener("click", async () => {
        const currentFlashcard = reviewQueue[currentIndex];
        if (confirm("Are you sure you want to delete this card?")) {
            await apiDelete(`/flashcards/${currentFlashcard.id}`);
            reviewQueue.splice(currentIndex, 1);
            await fillFrontAndBack();
        }
    });

    closeButton.addEventListener("click", () => {
        modal.style.display = "none";
    });

    editForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const currentFlashcard = reviewQueue[currentIndex];
        const updatedFlashcard = {
            front: editFront.value,
            back: editBack.value,
        };
        const newFlashcard = await apiPut(`/flashcards/${currentFlashcard.id}`, updatedFlashcard);
        reviewQueue[currentIndex] = newFlashcard;
        await fillFrontAndBack();
        modal.style.display = "none";
    });
}

async function showReviewFinishedMessage(){
    // if currentIndex is one smaller than length of rewviewQue, just display a message like "Congrats, finsihed review for this deck, next review due at ...."
    if(currentIndex >= reviewQueue.length){
        document.getElementById("reviewFinished").classList.add("show");
        return true;
    }
    document.getElementById("reviewFinished").classList.remove("show");
    return false;
}

async function backToStartButton(){
    const backToStart = document.getElementById("back-to-start");
    backToStart.addEventListener("click", () => {
        window.location.href = "start.html";
    })
}
async function startTimer(){
    startTime = new Date();
    const timer = document.getElementById("timer");
    timer.textContent = "0s";
    timer.style.color = "black";

    timeInterval = setInterval(() => {
        const elapsedSeconds = Math.floor(((new Date()) - startTime)/1000);
        timer.textContent = `${elapsedSeconds}s`;
    }, 1000); //do this every second 
}

async function stopTimer(){
    clearInterval(timeInterval);
    timeInterval = null;
    const elapsedSeconds  = Math.floor(((new Date()) - startTime) / 1000);
    const timer = document.getElementById("timer");
    timer.textContent = `${elapsedSeconds}s`;

    if(elapsedSeconds <= 5){
        timer.style.color = "green";
    }else if (elapsedSeconds <= 10){
        timer.style.color = "goldenrod";
    }else {
        timer.style.color = "red";
    }
}

// =====================
// Init
// =====================
let reviewQueue = [];
let currentIndex = 0;
let timeInterval = null;
let startTime = null;
document.addEventListener("DOMContentLoaded", async () => {
  if (!authToken) {
    window.location.href = "login.html";
    return;
  }
  try {

    const queryString = window.location.search; 
    const params = new URLSearchParams(queryString);
    const deckId = params.get("deckId");
    await showAndHideBack();
    reviewQueue =  await getDueFlashcards(deckId);
    await showReviewFinishedMessage(); //check if there are any cards to review
    await fillFrontAndBack();
    await sendFeedback();
    await backToStartButton();
    await cardActions();
  } catch (err) {
    console.error(err);
  }
});