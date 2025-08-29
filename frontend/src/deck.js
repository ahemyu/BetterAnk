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

// So we need to get all of the flashcards of the current deck, total and due (we need to do two calls to the backend)
// for that we need to know which deck we are in right now (identified by the deckid=n query parameter of the current url)

async function getNumberOfFlashcards() {
    const queryString = window.location.search; 
    const params = new URLSearchParams(queryString);
    if (params.has("deckId")){
        const deckId = params.get("deckId");
        // Now we have the deck ID and can just do the calls to the backenmd
        // first get all flashcards 
        const allFlashcards = await apiGet(`/decks/${deckId}/flashcards`);
        const numberofAllFlashcards = allFlashcards.length;
        
        const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
        const numberOfDueFlashcards = dueFlashcards.length;
        console.log(numberOfDueFlashcards);

    }    

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

  } catch (err) {
    console.error(err);
  }
});