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
  console.log("I WAS CALLED");
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
  document.getElementById("review-button").addEventListener("click", () => {
    window.location.href = "review.html"; //TODO: Adjust this ya salame
  });
}

async function backToDecks(){
  document.getElementById("back-to-dashboard").addEventListener("click", () => {
    window.location.href = "start.html";
  });
}

//TODO: add function that creates form to allow for users to create new flashcards for the current deck 

async function addFlashcardModal(){
  // clicking on button 'add-flashcard' removes 'hidden' class of 'flashcard-modal' to make it visible 
  const flashcardModalButton = document.getElementById("add-flashcard");
  const addFlashCardModal = document.getElementById("flashcard-modal");
  // add eventlistener for event click, 
  flashcardModalButton.addEventListener("click", () => {
    // remove hidden class 
    addFlashCardModal.classList.add("show");
  });

}
async function closeModal(){
  const addFlashCardModal = document.getElementById("flashcard-modal");
  const cancelButton = document.getElementById("add-flashcard-cancel");
  cancelButton.addEventListener("click", () => {
    addFlashCardModal.classList.remove("show"); 
  });
  // now if we click outside of the modal ,we wanna hide modal as well
  addFlashCardModal.addEventListener("click", (event) => {
    if(event.target === addFlashCardModal){
      addFlashCardModal.classList.remove("show");
    }
  });
  // if we press 'esc' key we also want to close the modal 
  document.addEventListener("keydown", (event) => {
    if(event.key === "Escape" && addFlashCardModal.classList.contains("show")){
      addFlashCardModal.classList.remove("show");
    }
  })
}

async function addNewCard() {
  const form = document.getElementById("add-flashcard-form");

  form.addEventListener("submit", async (event) => {
    event.preventDefault(); // stop form from refreshing the page

    const front = document.getElementById("front").value;
    const back = document.getElementById("back").value;

    const params = new URLSearchParams(window.location.search);
    let deckId = null;
    if (params.has("deckId")) {
      deckId = parseInt(params.get("deckId"));
    }

    const body = {
      front,
      back,
      deck_id: deckId,
    };

    console.log("Posting flashcard:", body);

    try {
      await apiPost("/flashcards", body);
      // After successful save:
      await getNumberOfFlashcards(); // refresh flashcard count
      // hide modal
      document.getElementById("flashcard-modal").classList.remove("show");
      // reset form fields
      form.reset();
    } catch (err) {
      console.error("Failed to add flashcard:", err);
    }
  });
}
// =====================
// Init
// =====================
// TODO: How can I run all of these in a loop? 
// right now after adding  a flashcard the whole dynamics get lost and the number of flashcards etc just go away.  
document.addEventListener("DOMContentLoaded", async () => {
  if (!authToken) {
    window.location.href = "login.html";
    return;
  }
  try {
    await getNumberOfFlashcards();
    await startReview();
    await backToDecks();
    await addFlashcardModal();
    await closeModal();
    await addNewCard();
  } catch (err) {
    console.error(err);
  }
});