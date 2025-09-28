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

async function displayDeckName(deckId){
  const deck = await apiGet(`/decks/${deckId}`);
  const deckName = deck.name;
  document.getElementById("deck-name").textContent = `${deckName}`
}

async function getNumberOfFlashcards() {
    const queryString = window.location.search; 
    const params = new URLSearchParams(queryString);
    if (params.has("deckId")){
        const deckId = params.get("deckId");
        displayDeckName(deckId);
        const allFlashcards = await apiGet(`/decks/${deckId}/flashcards`);
        const numberofAllFlashcards = allFlashcards.length;
        document.getElementById("all-flashcards").textContent = `${numberofAllFlashcards} total cards`
        
        const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
        const numberOfDueFlashcards = dueFlashcards.length;
        document.getElementById("due-flashcards").textContent = `${numberOfDueFlashcards} due cards`
    }    
}

async function startReview(){
  const queryString = window.location.search; 
  const params = new URLSearchParams(queryString);
  const deckId = params.get("deckId");
  document.getElementById("review-button").addEventListener("click", () => {
    window.location.href = `review.html?deckId=${deckId}`;
  });
}

async function backToDecks(){
  document.getElementById("back-to-dashboard").addEventListener("click", () => {
    window.location.href = "start.html";
  });
}

async function addFlashcardModal(){
  const flashcardModalButton = document.getElementById("add-flashcard");
  const addFlashCardModal = document.getElementById("add-flashcard-modal");
  flashcardModalButton.addEventListener("click", () => {
    addFlashCardModal.classList.remove("hidden");
  });
}

async function closeModal(){
  const addFlashCardModal = document.getElementById("add-flashcard-modal");
  const cancelButton = document.getElementById("add-flashcard-cancel");
  cancelButton.addEventListener("click", () => {
    addFlashCardModal.classList.add("hidden"); 
  });
  addFlashCardModal.addEventListener("click", (event) => {
    if(event.target === addFlashCardModal){
      addFlashCardModal.classList.add("hidden");
    }
  });
  document.addEventListener("keydown", (event) => {
    if(event.key === "Escape" && !addFlashCardModal.classList.contains("hidden")){
      addFlashCardModal.classList.add("hidden");
    }
  })
}

async function addNewCard() {
  const form = document.getElementById("add-flashcard-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const front = document.getElementById("front").value;
    const back = document.getElementById("back").value;
    const params = new URLSearchParams(window.location.search);
    let deckId = null;
    if (params.has("deckId")) {
      deckId = parseInt(params.get("deckId"));
    }
    const body = { front, back, deck_id: deckId };
    try {
      await apiPost("/flashcards", body);
      await getNumberOfFlashcards();
      form.reset();
      // also refresh the table view if it is open
      const showFlashcardsModal = document.getElementById("show-flashcards-modal");
      if (!showFlashcardsModal.classList.contains("hidden")) {
        await showAllFlashcards();
      }
    } catch (err) {
      console.error("Failed to add flashcard:", err);
    }
  });
}

async function showAllFlashcards() {
  const params = new URLSearchParams(window.location.search);
  const deckId = params.get("deckId");
  const flashcards = await apiGet(`/decks/${deckId}/flashcards`);
  const tbody = document.getElementById("flashcards-tbody");
  const rowTemplate = document.getElementById("flashcard-row-template");
  
  tbody.innerHTML = ""; // Clear existing rows

  for (const card of flashcards) {
    const row = rowTemplate.content.cloneNode(true);
    const tr = row.querySelector("tr");
    tr.dataset.flashcardId = card.id;
    row.querySelector(".front").textContent = card.front;
    row.querySelector(".back").textContent = card.back;
    row.querySelector(".next-review").textContent = new Date(card.next_review_at).toLocaleDateString();
    tbody.appendChild(row);
  }

  // Add event listeners for delete and edit buttons
  tbody.querySelectorAll(".delete-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
      const row = event.target.closest("tr");
      const flashcardId = row.dataset.flashcardId;
      try {
        await apiDelete(`/flashcards/${flashcardId}`);
        await getNumberOfFlashcards();
        await showAllFlashcards(); // Refresh the table
      } catch (err) {
        console.error("Failed to delete flashcard:", err);
      }
    });
  });

  tbody.querySelectorAll(".edit-btn").forEach(button => {
    button.addEventListener("click", (event) => {
      const row = event.target.closest("tr");
      const flashcardId = row.dataset.flashcardId;
      const front = row.querySelector(".front").textContent;
      const back = row.querySelector(".back").textContent;
      const nextReview = row.querySelector(".next-review").textContent;

      const editTemplate = document.getElementById("edit-flashcard-row-template");
      const editRowFragment = editTemplate.content.cloneNode(true);
      const editRow = editRowFragment.querySelector('tr');
      
      editRow.querySelector(".front-input").value = front;
      editRow.querySelector(".back-input").value = back;
      editRow.querySelector(".next-review").textContent = nextReview;
      
      row.replaceWith(editRow);

      editRow.querySelector(".save-btn").addEventListener("click", async () => {
        const newFront = editRow.querySelector(".front-input").value;
        const newBack = editRow.querySelector(".back-input").value;
        try {
          await apiPut(`/flashcards/${flashcardId}`, { front: newFront, back: newBack });
          await showAllFlashcards(); // Refresh the table
        } catch (err) {
          console.error("Failed to update flashcard:", err);
        }
      });

      editRow.querySelector(".cancel-edit-btn").addEventListener("click", () => {
        showAllFlashcards(); // Just refresh the table to cancel
      });
    });
  });
}

async function showAllFlashcardsModal() {
  const showFlashcardsButton = document.getElementById("show-flashcards");
  const showFlashcardsModal = document.getElementById("show-flashcards-modal");

  showFlashcardsButton.addEventListener("click", async () => {
    showFlashcardsModal.classList.remove("hidden");
    await showAllFlashcards();
  });
}

async function closeShowAllFlashcardsModal() {
    const showFlashcardsModal = document.getElementById("show-flashcards-modal");
    const cancelButton = document.getElementById("show-flashcards-cancel");

    cancelButton.addEventListener("click", () => {
        showFlashcardsModal.classList.add("hidden");
    });

    showFlashcardsModal.addEventListener("click", (event) => {
        if (event.target === showFlashcardsModal) {
            showFlashcardsModal.classList.add("hidden");
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !showFlashcardsModal.classList.contains("hidden")) {
            showFlashcardsModal.classList.add("hidden");
        }
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
    await getNumberOfFlashcards();
    await startReview();
    await backToDecks();
    await addFlashcardModal();
    await closeModal();
    await addNewCard();
    await showAllFlashcardsModal();
    await closeShowAllFlashcardsModal();
  } catch (err) {
    console.error(err);
  }
});