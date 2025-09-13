
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
    const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
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
    const noCardsLeft = await showReviewFinishedMessage();
    if(noCardsLeft == true){
        // we have to nullify the front and back and also not show the show answer button
        document.getElementById("show-review").style.display = "none";
        return;
    }
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
// =====================
// Init
// =====================
// =====================
console.log("HEREEEEEEEEEEEEE");
// document.getElementById("show-review").style.display = "block";
// document.getElementById("reviewFinished").classList.remove("show"); //Do not show the review finished message
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
    console.log(reviewQueue);
    await showReviewFinishedMessage(); //check if there are any cards to review
    await fillFrontAndBack();
    await sendFeedback();
    await backToStartButton();
  } catch (err) {
    console.error(err);
  }
});
