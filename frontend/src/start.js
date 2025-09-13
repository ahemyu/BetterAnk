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

async function apiDelete(path) {
  const res = await fetch(path, { method: "DELETE", headers });
  if (!res.ok) throw new Error(`DELETE ${path} failed`);
  return res.json();
}

// =====================
// UI Helpers
// =====================
function createDeckListItem(deck) {
  const li = document.createElement("li");
  const link = document.createElement("a");
  const deleteButton = document.createElement("button");
  // Need to add a <a> tag inside the li element that contains the 
  link.textContent = deck.name;
  link.href = `deck.html?deckId=${deck.id}`
  deleteButton.textContent = "❌";
  deleteButton.classList.add("delete-deck");
  deleteButton.dataset.id = deck.id;

  li.appendChild(link);
  li.appendChild(deleteButton);

  return li;
}

function renderDecks(decks) {
  const deckUl = document.querySelector("#decks-list");
  deckUl.innerHTML = ""; // clear old
  decks.forEach((deck) => deckUl.appendChild(createDeckListItem(deck)));
}

// =====================
// Page Logic
// =====================
async function loadUser() {
  const user = await apiGet("/me");
  document.getElementById(
    "welcome-message"
  ).textContent = `Welcome, ${user.username}!`;
}

async function loadDecks() {
  const decks = await apiGet("/decks");
  renderDecks(decks);
}

async function handleCreateDeck(event) {
  event.preventDefault();
  const name = document.getElementById("deck-name").value;
  const description = document.getElementById("deck-description").value;
  const newDeck = await apiPost("/decks", { name, description });
  document.querySelector("#decks-list").appendChild(createDeckListItem(newDeck));
  event.target.reset();
}

async function addCreateDeckModal(){
  const createDeckModalButton = document.getElementById("create-deck");
  const createDeckModal = document.getElementById("create-deck-modal");
  // add eventlistener for event click, 
  createDeckModalButton.addEventListener("click", () => {
    // remove hidden class 
    createDeckModal.classList.add("show");
  });

}

async function closeModal(){
  const createDeckModal = document.getElementById("create-deck-modal");
  const cancelButton = document.getElementById("create-deck-cancel");
  cancelButton.addEventListener("click", () => {
    createDeckModal.classList.remove("show"); 
  });
  // now if we click outside of the modal ,we wanna hide modal as well
  createDeckModal.addEventListener("click", (event) => {
    if(event.target === createDeckModal){
      createDeckModal.classList.remove("show");
    }
  });
  // if we press 'esc' key we also want to close the modal 
  document.addEventListener("keydown", (event) => {
    if(event.key === "Escape" && createDeckModal.classList.contains("show")){
      createDeckModal.classList.remove("show");
    }
  })
}

async function handleDeleteDeck(deckId) {
  await apiDelete(`/decks/${deckId}`);
  loadDecks(); // refresh list, seems kinda inefficient but fine for most users (very few users would have more than 5 decks anyways)
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
    await loadUser();
    await loadDecks();
  } catch (err) {
    console.error(err);
    localStorage.removeItem("authToken");
    window.location.href = "login.html";
    return;
  }

  await addCreateDeckModal();
  await closeModal();

  document
    .getElementById("create-deck-form")
    .addEventListener("submit", handleCreateDeck);

  document
    .getElementById("decks-list")
    .addEventListener("click", (event) => {
      if (event.target.classList.contains("delete-deck")) {
        handleDeleteDeck(event.target.dataset.id);
      }
    });

  document.getElementById("logout-link").addEventListener("click", () => {
    localStorage.removeItem("authToken");
  });
});