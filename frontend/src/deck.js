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

// =====================
// Page Logic
// =====================

async function displayDeckName(deckId){
  const deck = await apiGet(`/decks/${deckId}`);
  const deckName = deck.name;
  document.getElementById("deck-name").textContent = `${deckName}`
}

// So we need to get all of the flashcards of the current deck, total and due (we need to do two calls to the backend)
// for that we need to know which deck we are in right now (identified by the deckid=n query parameter of the current url)
async function getNumberOfFlashcards() {
    const queryString = window.location.search; 
    const params = new URLSearchParams(queryString);
    if (params.has("deckId")){
        const deckId = params.get("deckId");
        displayDeckName(deckId);
        // Now we have the deck ID and can just do the calls to the backenmd
        // first get all flashcards 
        const allFlashcards = await apiGet(`/decks/${deckId}/flashcards`);
        const numberofAllFlashcards = allFlashcards.length;
        document.getElementById("all-flashcards").textContent = `${numberofAllFlashcards} total cards`
        
        // then due flashcards
        const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
        const numberOfDueFlashcards = dueFlashcards.length;
        document.getElementById("due-flashcards").textContent = `${numberOfDueFlashcards} due cards`
    }    
}

async function startReview(){
  //this just needs to link to review page basically which should display all due flashcards one after the other
  document.getElementById("re
    view-button").addEventListener("click", () => {
    window.location.href = "review.html"; //TODO: Adjust this ya salame
  });
}

async function backToDecks(){
  document.getElementById("back-to-dashboard").addEventListener("click", () => {
    window.location.href = "start.html";
  });
}

// =====================
// Init
// =====================
document.addEventListener("DOMContentLoaded", async () => {
  if (!authToken) {
    window.location.href = "login.html";
    return;
  }

  try {
    getNumberOfFlashcards();
    startReview();
    backToDecks();

  } catch (err) {
    console.error(err);
  }
});