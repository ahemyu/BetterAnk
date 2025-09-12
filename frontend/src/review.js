
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

// =====================
// Page Logic
// =====================

// we need to do backend call to get the number of due flashcards

async function getDueFlashcards(deckId){
    const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards`);
    //TODO: sort based on next_review_at
}

//TODO: eventhandler to show back once user clicks enter or the "Show Answer" button

// =====================
// Init
// =====================


document.addEventListener("DOMContentLoaded", async () => {
  if (!authToken) {
    window.location.href = "login.html";
    return;
  }
  try {
    const queryString = window.location.search; 
    const params = new URLSearchParams(queryString);
    const deckId = params.get("deckId");
    await getDueFlashcards(deckId);

  } catch (err) {
    console.error(err);
  }
});
