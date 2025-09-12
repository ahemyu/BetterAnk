
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

// =====================
// Page Logic
// =====================

async function getDueFlashcards(deckId){
    const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards`);
    dueFlashcards.sort((a,b) => new Date(a.next_review_at) - new Date(b.next_review_at));

    return dueFlashcards;
}

async function showAndHideBack(){
    // add eventhanlder for the show answer button 
    const showAnswerButton = document.getElementById("show-answer");
    const backDiv = document.getElementById("back");
    showAnswerButton.addEventListener("click", () => {
        backDiv.classList.add("show");
    });
}

async function fillFrontAndBack(){
    const frontP = document.getElementById("front-p");
    const backP = document.getElementById("back-p");
    
    // use the global currentIndex to determione which flahcrad we are looking at 
    const currentFlashcard = reviewQueue[currentIndex];
    frontP.textContent = currentFlashcard.front;
    backP.textContent = currentFlashcard.back;
}

async function sendFeedback(){
    // we need to get the curernt flashcard"s id (referencing the global variable) 
    const badFeedbackButton = document.getElementById("bad");
    const midFeedbackButton = document.getElementById("mid");
    const goodFeedbackButton = document.getElementById("good");
    const currentFlashcard = reviewQueue[currentIndex];

    badFeedbackButton.addEventListener("click", async () => {
        await apiPost(`/flashcards/${currentFlashcard.id}/review`, {"feedback": "bad"});
        currentIndex++;
    });
   midFeedbackButton.addEventListener("click", async () => {
        await apiPost(`/flashcards/${currentFlashcard.id}/review`, {"feedback": "mid"});
        currentIndex++;
    });
    goodFeedbackButton.addEventListener("click", async () => {
        await apiPost(`/flashcards/${currentFlashcard.id}/review`, {"feedback": "good"});
        currentIndex++;
    });

}   

// =====================
// Init
// =====================
// =====================

let reviewQueue = [];
let currentIndex = 0;
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
    await fillFrontAndBack();
    await sendFeedback()
    // TODO need to call the function that willl populate front and back accordingly based on current flashcard 
  } catch (err) {
    console.error(err);
  }
});
