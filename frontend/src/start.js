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
  const nameSpan = document.createElement("span");
  const deleteButton = document.createElement("button");

  nameSpan.textContent = deck.name;
  deleteButton.textContent = "❌";
  deleteButton.classList.add("delete-deck");
  deleteButton.dataset.id = deck.id;

  li.appendChild(nameSpan);
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